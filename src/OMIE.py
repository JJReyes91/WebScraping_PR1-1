# Importamos librerías necesarias
import requests
from bs4 import BeautifulSoup
import time
import datetime as dt
import re
import pandas as pd

class OMIEdata():
    # Constants
    URL_BASE = 'http://www.omie.es/aplicaciones/datosftp/datosftp.jsp?path=/'
    DELAY = 10
    TIMEOUT = 20
    
    def __init__(self, start_date='2018-10-01', end_date='2018-10-02'):
        """
        Iniciliza la clase OMIEdata a partir de una lista de variables objetivo
        y un rango de fechas, ejecutando el webscrapping de los datos en omie.es
        """
        self._filename = 'OMIE_' + ''.join(start_date.split('-')) + '_' + ''.join(end_date.split('-')) + '.csv'
        
        # Inicializamos fechas como datetime
        self.start_date = dt.datetime.strptime(str(start_date), "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(str(end_date), "%Y-%m-%d")
        
        # Creamos un diccionario que vamos a usar para tipificar las entidades
        # que tenemos controladas con su tipo de tabla origen y su tipo de tabla final
        self.var_dict = {'marginalpdbc':[1,1],
                         'marginalpdbcpt':[1,1],
                         'pdbc_tot':[2,1]}
        
        
        # inicializamos las variables objetivos de manera estatica ya que
        # para nuevas variables habria que crear nuevos metodos
        self.variables = list(self.var_dict.keys())
        
        # inicializamos la variable interna tlast (ultima request, solicitada)
        self._tlast = time.clock()
        
        # inicializamos un diccionario de tries vacios, para Timeouts y Connection Failed
        self._dict_tries = {}
        
        # Ejecutamos web scraping
        self.__execute()
        
    
    def __getDataframe1(data):
        """
        Devuelve un dataframe de pandas a partir de una tabla de datos en formato
        de texto plano con separador de ;
        
        Es el tipo de formato de origen 1
        """
        # separamos la tabla en filas
        rows = data.split(';\r\n')
        
        # Definimos los nombres de las columnas
        date_cols = ['year', 'month', 'day', 'hour']
        val_cols = [rows[0]+'_1', rows[0]+'_2']
        
        df = pd.DataFrame([x.split(';') for x in rows[1:-1]],
                           columns = date_cols + val_cols)
        
        df = df.apply(pd.to_numeric, errors='coerce')
        
        df['timestamp'] = pd.to_datetime(df[date_cols])
        
        df.index = df['timestamp'] - dt.timedelta(hours=1)
        
        return df[val_cols]

    def __getDataframe2(data):
        """
        Devuelve un dataframe de pandas a partir de una tabla de datos en formato
        de texto plano con separador de ;
        
        Es el tipo de formato de origen 2
        """
        df = pd.DataFrame({})
        rows = data.split('\r\n')
        
        for row in rows[3:-2]:
            row = row.split(';')
            colname = row[0]+'_'+row[1]
            df[colname] = row[2:-2]
            
        date = dt.datetime.strptime(str((rows[0].split(';'))[3]), "%d/%m/%Y")
        
        df = df.set_index(pd.DatetimeIndex(start = date, freq ='H', end = date + dt.timedelta(hours=23)))
        
        for col in df.columns:
            df[col] = [x.replace('.', '') for x in df[col]]
            df[col] = [x.replace(',', '.') for x in df[col]]
        
        
        return df

    def __getDateFromTag(tag):
        """
        Funcion que obtiene la fecha en formato 
        YYYYMMDD a partir de un link
        """
        # Extraemos la fecha del string del link y la pasamos a datetime
        date = re.search('.*([0-9]{8}).*', tag.text)
        date = dt.datetime.strptime(str(date.group(1)), "%Y%m%d")
    
        return date
    
    def __execute(self):
        """
        Ejecuta el WebScraping
        """
        # inicializamos una lista total de df
        lista = []
        # iteramos sobre las variables para obtener el dataframe de cada una
        for var in self.variables:
            if self.var_dict[var][1] == 1:
                lista.append(self.__getVariable(var))
        
        
        self.df = lista[0]
        for dfr in lista[1:]:
           self.df = self.df.join(dfr) 
          
        self.df = self.df.drop(self.df.columns[[4,7,8,11,12,15]], axis=1, inplace=True)
        self.df.to_csv(self._filename)
                
    
    def __getVariable(self, var):
        """A partir de una magnitud válida y unas fechas de inicio y final
        devuelve un dataframe con todos los datos de dicha magnitud para
        las fechas especificadas.
        
        Dentro de OMIE cada magnitud/fecha es una URL distinta
        """
        # obtenemos los links de descarga mediante scraping
        links = self.__getLinks(var)
    
        df_list = []
        for url in links:
            # Obtenemos el html y lo cargamos como sopa
            r = self.__getRequest(url)
            soup = BeautifulSoup(r.text, 'lxml')

            # Buscamos el elemento p, y obtenemos su contenido
            data = soup.find('p').contents[0]
            
            # creamos un dataframe a partir del contenido extraido
            # y lo añadimos a la lista de df
            if self.var_dict[var][0] == 1: 
                df_list.append(OMIEdata.__getDataframe1(data))
            elif self.var_dict[var][0] == 2:
                df_list.append(OMIEdata.__getDataframe2(data))
        
        # concatenamos todos los df (cada uno de un dia) y devolvemos
        return pd.concat(df_list)
    
    def __getLinks(self, var):
        """
        Obtiene los links para un variable determinada y una fechas
        """
        # Configuramos la url destino
        url = self.URL_BASE + var + '/'
        
        # Descargamos el html
        r =self.__getRequest(url)
        
        # Creamos la soup
        soup = BeautifulSoup(r.text, 'html.parser')
    
        # Obtenemos todos los tags <a>, en orden inversa
        tags = list(reversed(soup.find_all('a')))
        
        # Extraemos la fecha del string del link y la pasamos a datetime
        last_date = re.search('.*([0-9]{8}).*', tags[0].text)
        last_date = dt.datetime.strptime(str(last_date.group(1)), "%Y%m%d")
        
        # Calculamos los indices de los dias target
        ind1 = (last_date-self.end_date).days
        ind2 = (last_date-self.start_date).days
        
        # Guardamos los tags que queremos
        tags = tags[ind1:ind2+1]
        
        # Extraemos los links de los tags target
        links = [tag.get('href') for tag in tags]
            
        return links
        
    def __getRequest (self, url):
        """
        Descargamos la página web solicitada en el url
        con un delay entre descargas segun la variable de clase _delay
        y con excepciones capturadas para los casos de 
        TimeOut y Fallo en la Conexion
        """
        # pasamos el tiempo entre requests a tnow
        self._tnow = time.clock()
        
        # Comprobamos que hayan pasado delay s desde la ultima vez, y sino esperamos
        if (self._tnow-self._tlast) < self.DELAY: 
            time.sleep(self.DELAY - (self._tnow-self._tlast))
        
        try:
            # Realizamos la request con 20s de timeout y headers personalizados
            html = requests.get(url, timeout = self.TIMEOUT)
            
            #  Actualizamos el tiempo de ultima request solicitada a la web
            self._tlast = time.clock()
            
            # Comprobamos que el status de la request sea 200 y devolvemos con warning si no es así
            if html.status_code != 200:
                print("STATUS CODE {} on {}. Check it out.".format(html.status_code,url))
            else:
                print("ALL GOOD for {}".format(url))
            return html
        
        except requests.exceptions.Timeout:
            print("TIMEOUT on {}.".format(url))
            tries = 0
            # wait and retry it
            if tries < 2:
                time.sleep(10)
                self.__getRequest(url)
                tries += 1
    
        except requests.exceptions.RequestException:
            print("Connection Failed on {}.".format(url))
            tries = 0
            # wait and retry it
            if tries < 2:
                time.sleep(10)
                self.__getRequest(url)
                tries += 1