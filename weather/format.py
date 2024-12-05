import importlib.resources
import json

import utils
from utils import convert

# NOTE Later on should be moved into some sort of translations module with getters

CURRENT_PACKAGE_NAME = 'weather'
CUSTOM_DATA_FILE_NAME = 'custom-data.json'

with importlib.resources.open_text(CURRENT_PACKAGE_NAME, CUSTOM_DATA_FILE_NAME) as file:
    # Getting type hints off of it would be nice
    # TODO Внести в файл величины
    custom_data = json.load(file)

# TODO Should rename to something like NumericValue
class Value():
    def __init__(self, value, unit:str, accuracy:int=2, separator:str=' ') -> None:
        self.set_value(value)
        self.set_unit(unit)
        self.set_accuracy(accuracy)
        self.set_separator(separator)
    
    def set_value(self, value):
        self.value = value

    def set_unit(self, unit:str):
        # TODO Short / long versions ?
        self.unit = unit

    def set_accuracy(self, accuracy:int):
        self.accuracy = accuracy

    def set_separator(self, separator:str):
        self.separator = separator

    def get_value(self, accuracy:int=None) -> float:
        if accuracy is None: accuracy = self.accuracy

        if accuracy == 0:
            return int(self.value)

        # FIXME Python leaves .0 to the end of numbers after round sometimes
        # REMOVE THE ABOVE IF WHEN FIXED
        return round(self.value, accuracy)

    def get_str(self, separator:str=None, accuracy:int=None) -> str:
        if separator is None: separator = self.separator

        value = self.get_value(accuracy)
        unit = self.unit

        return separator.join([str(value), unit])

class Temperature():
    def __init__(self, k:float=None) -> None:
        self.c = Value(convert.k_to_c(k), '°C', 1)
        self.f = Value(convert.k_to_f(k), '°F', 1)
        self.k = Value(k, 'K', 0)

class TemperatureData():
    def __init__(
            self,
            actual:Temperature,
            min:Temperature,
            max:Temperature,
            feels_like:Temperature,
        ) -> None:

        self.actual = actual
        self.min = min
        self.max = max
        self.feels_like = feels_like

class Pressure():
    def __init__(self, mbar:float=None) -> None:
        self.hpa = Value(mbar, 'hPa', 0)
        self.mmhg = Value(convert.mbar_to_mmhg(mbar), 'mmHg', 0)
        self.mbar = Value(mbar, 'Mbar', 0)

class PressureData():
    def __init__(
            self,
            sea_level:Pressure,
            ground_level:Pressure,
        ) -> None:

        self.sea_level = sea_level
        self.ground_level = ground_level

        self.index = convert.get_pressure_index(self.ground_level.mmhg.get_value())
        self.name = custom_data['pressure'][self.index]

class Speed():
    def __init__(self, ms:float=0, accuracy:int=1) -> None:
        
        self.ms = ms

        self.set_accuracy(accuracy)
    
    def set_accuracy(self, accuracy:int):
        self.accuracy = accuracy

        self.set_ms(self.ms)

    def set_ms(self, ms:float):
        self.ms = Value(ms, 'ms', 1)
        self.kph = Value(convert.ms_to_kph(ms), 'kph', 1)
        self.mph = Value(convert.ms_to_mph(ms), 'mph', 0)
        self.knots = Value(convert.ms_to_knots(ms), 'knots', 0)

class CardinalPoint():
    def __init__(self, degree:float) -> None:

        cardinal_point = custom_data['cardinal_points'][convert.degree_to_cardinal_point_id(degree)]

        self.short:str = cardinal_point['short']
        self.long:str = cardinal_point['long']

class Wind():
    def __init__(self, speed:Speed, gusts:Speed, degree:float) -> None:
        self.speed = speed
        self.gusts = gusts

        self.beaufort_scale = utils.clamp(convert.knots_to_beaufort_scale_index(speed.knots.value), 0, 17)
        self.name:str = custom_data['wind'][self.beaufort_scale]

        self.degree = Value(degree, '°', 0, '')
        self.cardinal_point = CardinalPoint(degree)

class Timezone():
    def __init__(self, offset_ms:int=0) -> None:
        self.set_offset(offset_ms)
    
    # TODO Should add such setters to the rest of the classes
    # Or predent like it was never here, bc im not gonna use them anyway
    def set_offset(self, ms:int=0) -> None:
        self.offset = ms

class Visibility():
    def __init__(self, m:float) -> None:
        self.m = Value(m, 'm', 0)
        self.km = Value(m/1000, 'km', 1)
        self.mi = Value(convert.m_to_mi(m), 'miles', 3)

        self.index = convert.get_visibility_index(self.m.get_value())
        self.name:str = custom_data['visibility'][self.index]

class Humidity():
    def __init__(self, humidity:int) -> None:
        self.percentage = Value(humidity, '%', 0, '')
        
        self.index = convert.get_humidity_index(humidity)
        self.name:str = custom_data['humidity'][self.index]
    
    def get_str(self, separator:str=None, accuracy:int=None) -> str:
        output = self.name

        if not self.index in [0, 4]:
            output += f' {self.percentage.get_str(separator=separator, accuracy=accuracy)}'
        
        return output

class Cloudiness():
    def __init__(self, cloudiness:int) -> None:
        self.percentage = Value(cloudiness, '%', 0, '')
        
        self.index = convert.get_cloudiness_index(cloudiness)
        self.name:str = custom_data['cloudiness'][self.index]
    
    def get_str(self, separator:str=None, accuracy:int=None) -> str:
        output = self.name

        if not self.index in [0, 4]:
            output += f' {self.percentage.get_str(separator=separator, accuracy=accuracy)}'
        
        return output

class Weather():
    def __init__(
            self,

            title:str,
            description:str,
            weather_code:str,
            default_icon_url:str,

            temperature:TemperatureData,
            wind:Wind,

            humidity:Humidity,
            pressure:PressureData,
            clouds:Cloudiness,
            visibility:Visibility,

            sunrise:int,
            sunset:int,
            timezone:Timezone,
        ) -> None:

        self.title = title
        self.description = description
        self.weather_code = weather_code
        self.default_icon_url = default_icon_url

        self.temperature = temperature
        self.wind = wind

        self.humidity = humidity
        self.pressure = pressure
        self.clouds = clouds
        self.visibility = visibility

        self.sunrise = sunrise
        self.sunset = sunset
        self.timezone = timezone
    
    # I believe it was used for testing
    # def get_str(self) -> str:
    #     return f'{self.title}, {self.description}. {self.temperature.actual.c.get_str()}, {self.wind.speed.ms.get_str()}.'

def format_data(raw_data:dict) -> Weather:
    # Not partly raw, but medium rare
    return Weather(
        title = raw_data['weather'][0]['main'],
        description = raw_data['weather'][0]['description'],

        temperature = TemperatureData(
            actual = Temperature(raw_data['main']['temp']),
            min = Temperature(raw_data['main']['temp_min']),
            max = Temperature(raw_data['main']['temp_max']),
            feels_like = Temperature(raw_data['main']['feels_like']),
        ),
        wind = Wind(
            speed = Speed(raw_data['wind']['speed']),
            gusts = Speed(raw_data['wind']['gust'] if 'gust' in raw_data['wind'] else raw_data['wind']['speed']),
            degree = raw_data['wind']['deg'],
        ),
        weather_code = raw_data['weather'][0]['id'],
        default_icon_url = f'https://openweathermap.org/img/wn/{raw_data["weather"][0]["icon"]}@2x.png',

        humidity = Humidity(raw_data['main']['humidity']),
        pressure = PressureData(
            sea_level = Pressure(raw_data['main']['sea_level']),
            ground_level = Pressure(raw_data['main']['grnd_level']),
        ),
        clouds = Cloudiness(raw_data['clouds']['all']),
        visibility = Visibility(raw_data['visibility']),

        sunrise = raw_data['sys']['sunrise'],
        sunset = raw_data['sys']['sunset'],
        timezone = Timezone(raw_data['timezone']),
    )