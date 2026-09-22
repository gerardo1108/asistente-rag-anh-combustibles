"""Compara imágenes RAG en contenedores temporales; no modifica servicios activos.

Requiere Docker y .env con Groq. Cada ronda realiza una consulta real al LLM.
Los límites se aplican al contenedor; las mediciones son locales, no Cloud Run.
"""
import argparse
import json
import statistics
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

MEMORIA = '''import json
from pathlib import Path
s=Path('/proc/1/status').read_text().splitlines()
rss=int(next(x for x in s if x.startswith('VmRSS:')).split()[1])*1024
print(json.dumps({'rss_bytes':rss,'cgroup_current_bytes':int(Path('/sys/fs/cgroup/memory.current').read_text()),'cgroup_peak_bytes':int(Path('/sys/fs/cgroup/memory.peak').read_text())}))'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--images', nargs='+', required=True)
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--memory', default='2g')
    parser.add_argument('--cpus', default='1')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()

    def docker(*cmd):
        return subprocess.check_output([args.docker, *cmd], text=True, stderr=subprocess.PIPE).strip()

    resultados = {'cpus':args.cpus, 'memory_limit':args.memory,
                  'rounds':args.rounds, 'runtime_offline_embeddings':True, 'imagenes':[]}
    for imagen in args.images:
        info = json.loads(docker('image', 'inspect', imagen, '--format', '{{json .}}'))
        entry = {'imagen':imagen, 'id':info['Id'], 'size_bytes':info['Size'],
                 'architecture':info['Architecture'], 'mediciones':[]}
        resultados['imagenes'].append(entry)
        for ronda in range(args.rounds):
            nombre = 'anh-medicion-' + uuid.uuid4().hex[:10]
            inicio = time.monotonic()
            try:
                docker('run', '-d', '--name', nombre, '--cpus', args.cpus, '--memory', args.memory,
                       '--env-file', str(args.env_file.resolve()), '-e', 'HF_HUB_OFFLINE=1',
                       '-e', 'TRANSFORMERS_OFFLINE=1', '-p', '127.0.0.1::8003', imagen)
                puerto = docker('port', nombre, '8003/tcp').rsplit(':', 1)[1]
                base = 'http://127.0.0.1:' + puerto
                while time.monotonic() - inicio < 180:
                    try:
                        with urlopen(base+'/docs', timeout=1) as r:
                            if r.status == 200: break
                    except (URLError, TimeoutError, ConnectionError):
                        if docker('inspect', nombre, '--format', '{{.State.Running}}') != 'true':
                            raise RuntimeError('El contenedor terminó antes de estar listo')
                        time.sleep(0.25)
                else:
                    raise RuntimeError('Tiempo de arranque superior a 180 s')
                arranque = round(time.monotonic()-inicio, 3)
                reposo = json.loads(docker('exec', nombre, 'python', '-c', MEMORIA))
                datos = {'pregunta':'¿Qué información mínima es obligatoria en el Formulario Electrónico?'}
                request = Request(base+'/v1/consultas-rag', data=json.dumps(datos).encode(),
                                  headers={'Content-Type':'application/json'})
                inicio_peticion = time.monotonic()
                with urlopen(request, timeout=90) as r: salida = json.load(r)
                latencia = round(time.monotonic()-inicio_peticion, 3)
                assert salida['encontrado'] and salida['fuentes'] and salida['proveedor_llm']=='groq'
                posterior = json.loads(docker('exec', nombre, 'python', '-c', MEMORIA))
                dato = {'ronda':ronda+1,'arranque_segundos':arranque,'reposo':reposo,
                        'consulta_segundos':latencia,'despues_consulta':posterior,'respuesta_con_fuentes':True}
                entry['mediciones'].append(dato)
                print(imagen, json.dumps(dato), flush=True)
            finally:
                subprocess.run([args.docker, 'rm', '-f', nombre], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, check=False)
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps(resultados, indent=2)+'\n')
        entry['mediana_arranque_segundos'] = statistics.median(x['arranque_segundos'] for x in entry['mediciones'])
        args.report.write_text(json.dumps(resultados, indent=2)+'\n')


if __name__ == '__main__':
    main()
