# WebScraping_PR1 - Pablo Lombao Vázquez

## Descripción

Práctica enmarcada dentro de la asignatura Tipología y ciclo de vida de los datos correspondiente al máster en Data Science de la Universitat Oberta de Catalunya mediante la que se genera un dataset con un histórico de datos con los precios de la energía publicados por la OMIE mediante técnicas de webscraping.

## Ficheros

+ /src/OMIE.py: documento con la implementación de la clase OMIEdata para realizar el web scraping
+ /src/main.py: documento principal para lanzar la ejecución con las fechas (en formato YYYY-MM-DD)
+ /data/OMIE_20180601_20181020.csv: fichero csv con el dataset obtenido
+ /PR1_LombaoVazquez_Pablo.pdf: documento pdf con las respuestas de la Práctica
+ /Precio_horario.png: gráfica incluida en el documento pdf

## Consideraciones

El fichero tiene un **tiempo de ejecución muy alto** para fechas largas porque tiene programado un **retraso de 10 segundos entre request**, para cumplir con las condiciones especificadas en el robots.txt de omie.es. Por cada día se acceden a 3 variables distintas, cada una con un índice, por tanto, para n días, el script tarda de mínimo 30(n+1) segundos.

## Recursos

* Subirats, L., Calvo, M. (2018). Web Scraping. Editorial UOC.
* Lawson, R. (2015). Web Scraping with Python. Packt Publishing Ltd. Chapter 2. Scraping the Data.
