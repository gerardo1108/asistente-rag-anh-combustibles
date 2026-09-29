# Preguntas de prueba manual para el RAG

20 preguntas para evaluar en vivo las respuestas del servicio RAG (pestaña
"Consultar" del chat), divididas por categoría según la normativa aplicada
(Decreto Supremo N° 5400 y Resolución Administrativa RAN-ANH-DJ-UGJN
N° 0008/2025). A diferencia de `golden_set.json` (que solo prueba retrieval,
sin LLM, vía `evaluar_retrieval.py`), esta lista es para revisión manual del
pipeline completo — retrieval y generación.

## Categoría 1: Requisitos de Registro y Formulario Electrónico

1. «Hola, necesito comprar un poco de gasolina en un bidón. ¿Qué trámite
   tengo que hacer primero para que me la vendan?»
2. «¿Qué datos o documentos me van a pedir al momento de llenar el
   formulario para comprar en bidón?»
3. «¿Tengo que sacarme alguna foto o subir imágenes al momento de registrar
   el formulario?»
4. «¿Puedo hacer el registro desde mi celular en mi casa o me lo tienen que
   hacer en la misma estación de servicio?»
5. «Si ya hice mi declaración jurada en el formulario, ¿con qué documento me
   identifico cuando llegue al dispensador de la gasolinera?»

## Categoría 2: Límites de Volumen y Subvención de Precio

6. «¿Cuántos litros de diésel puedo comprar al mes como máximo en bidón para
   mi trabajo?»
7. «Vivo cerca de la frontera, ¿aplica la misma cantidad de litros que en la
   ciudad o hay un límite distinto para zonas fronterizas?»
8. «¿Puedo comprar la gasolina al precio subvencionado habitual si la llevo
   en un envase o bidón?»
9. «Si no lleno el formulario electrónico, ¿de todos modos me pueden vender
   combustible en un bidón?»
10. «Si decido comprar sin hacer el formulario electrónico, ¿cuánto
    combustible me dejan llevar y a qué precio me lo van a cobrar?»

## Categoría 3: Casos de Uso y Tipo de Envases

11. «¿En qué tipo de recipientes o envases está permitido llevar la gasolina
    o diésel? ¿Sirve cualquier botella o balde?»
12. «Si necesito combustible para una motobomba o maquinaria agrícola, ¿qué
    debo colocar en la casilla de 'destino de uso' del formulario?»
13. «¿Puedo comprar diésel en bidón para un auto que funciona a GNV si
    excedí mi cupo mensual?»
14. «Si ya compré 120 litros este mes con mi formulario, ¿puedo volver a
    comprar más volumen en el mismo mes si pago precio internacional?»

## Categoría 4: Validez, Proceso Legal y Excepciones

15. «¿Qué implicaciones legales tiene el formulario que lleno? ¿Qué pasa si
    me equivoco en la información que pongo sobre el uso del combustible?»
16. «¿Cada cuánto tiempo tengo que renovar mi registro en el Formulario
    Electrónico para seguir comprando en bidones?»
17. «¿Necesito estar registrado en la Ciudadanía Digital de la AGETIC
    obligatoriamente para poder sacar el formulario de la ANH?»
18. «¿Qué pasa si en la estación de servicio se corta el internet y no
    pueden verificar mi formulario electrónico?»

## Categoría 5: Preguntas Trampa / Borde (Edge Cases para medir al RAG)

19. «Mi hermano no puede ir a la gasolinera, ¿puedo ir yo llevando su cédula
    de identidad y su formulario impreso para que me vendan el diésel a su
    nombre?»
20. «¿Puedo usar la app de Ciudadanía Digital para validar mi identidad al
    momento de comprar el diésel en el bidón si no llevé mi carnet físico?»
