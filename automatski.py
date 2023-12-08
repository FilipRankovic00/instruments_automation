from typing import Optional
from PySide6.QtWidgets import (QLineEdit)
from PySide6.QtGui import QFont, QCursor
from PySide6 import QtCore
from PySide6.QtCore import Qt, QObject, QThread, Signal, QTimer

from Fluke8846A import Fluke8846A
from Fluke9142 import Fluke9142
from Isotech954 import Isotech954


import pyvisa
import time, threading

# FLUKE 8846A device_info

# FLUKE 9142 device_info

# ISOTECH 954 device_info


def automatskiUI(range_combo, range_label, nominal_temperature, temperature_label, expected_value, widgets):
  range_combo.setHidden(True)
  range_label.setHidden(True)
  # range_combo.activated.connect(lambda: promena(True))

  temperature_label.move(235, temperature_label.y())
  temperature_label.setText('Zadaj temperaturu i klikni ETALONIRAJ:')  
  nominal_temperature.move(346, nominal_temperature.y() + 20)
  expected_value.move(190, expected_value.y() + 15)

  for item in widgets:
    item.move(item.x(), item.y() + 35)

    if(isinstance(item, QLineEdit)):
      item.setReadOnly(True)

class Stability(QObject):

  finished = Signal()

  def __init__(self, multimetar, kalibrator, selektor, parent = None) -> None:
    super(Stability, self).__init__(parent)
    self.multimetar = multimetar  
    self.kalibrator = kalibrator
    self.selektor = selektor
          
  
  def setInterval(self, interval = 3000):
    self.timer = QTimer()
    self.timer.timeout.connect(self.__checkStability)
    self.timer.start(interval)   
    
  def __checkStability(self):          
    # PROVERITI DA LI SE ZONA STABILIZOVALA
    # Funkcija iz biblioteke koja vraca 1 ako je stabilnost zone u zadatim okvirima
    
    
    if self.kalibrator.get_stability_of_controller():
      # Timer stop da ne uleti ponovo u funkciju
      self.timer.stop()
      # Saceka se jos 10s da se dodatno stabilizuju sonde
      time.sleep(10)
      # Komanda za pocetak merenja (???)
      self.multimetar.trigger_measurment() # Dodao novu metodu u biblioteku: return self.__write_data('*TRG')
      time.sleep(2)
      # Fetch podataka sa displeja 1 (default)
      data = self.multimetar.fetch_data()      
      print(data) # VIDETI STA SE DOBIJA U TERMINALU -> STAVITI U []
      self.selektor.switch_to_channel(2)
      time.sleep(5)
      self.multimetar.trigger_measurment()
      time.sleep(2)
      data_2 = self.multimetar.fetch_data()
      print(data_2)      
      
      self.kalibrator.set_output_off()
      self.finished.emit()
      return

  def transferData(self, data):
    pass


  def stop(self):
    self.timer.stop()

class Th():
  def __init__(self, multimetar, kalibrator, selektor) -> None:
    self.thread = QThread()
    # Preko konstruktora se prebacuju argumenti na Worker - instance klasa koje su ranije napravljene u AutomatskoEtaloniranje 
    self.worker = Stability(multimetar, kalibrator, selektor)    

  def move_to_thread(self):    

    self.worker.moveToThread(self.thread)
    self.thread.started.connect(self.worker.setInterval)
    self.worker.finished.connect(self.thread.quit)
    self.thread.finished.connect(self.thread.deleteLater)
    self.thread.start()

# Mora da se inicijalizuje neka global promenljiva inace nece da krene QThread
thread = None

class AutomatskoEtaloniranje(QObject):
  def __init__(self, nominal_temperature, start_calibration) -> None:
    super().__init__()
    self.nominal_temperature = nominal_temperature
    self.start_calibration = start_calibration
    self.mutlimeter_setup()
    self.selector_setup()
    self.calibrator_setup()

  def devices_info(self):
    self.rm = pyvisa.ResourceManager()
    print(self.rm.list_resources())

  def mutlimeter_setup(self):
    # DEV INFO !
    self.multimeter = Fluke8846A('', read_termination='\n', write_termination='\n', timeout = 100_000)
    self.multimeter.clear_status()
    # Podesavanje za cetvorozicno merenje 
    self.multimeter.set_4w_resistance('DEF', 'MAX')
    # Komanndom *TRG pokrecem merenje (???)
    self.multimeter.set_trigger_source('BUS')
    
    # Mozda treba staviti neki delay da se ne citaju odmah podaci nego da se saceka jos malo (reseno u thread-u sa sleep i ne blokira)

    self.multimeter.set_trigger_delay()    

    # Dva trigera - za dve sonde tj. dva merenja po 10 pre nego sto ode u idle
    self.multimeter.set_trigger_count(2)
    
    # 10 uzastopnih merenja - POTREBNO SMESTITI U LISTU 10 ELEMENATA ! 
    self.multimeter.set_samples_per_trigger(10)

    # Odmah po pristizanju *TRG komande se vrsi merenje (???)
    self.multimeter.init_wait_for_triger()

  def selector_setup(self):
    # DEV INFO !
    self.selector = Isotech954('')
    self.selector.switch_to_channel(1)   
    
  def calibrator_setup(self):    
    # DEV INFO !
    self.calibrator = Fluke9142('')

    # Stabilnost temperature u zoni
    self.calibrator.set_stability_limit(0.05)

    # Temperatura zadata preko UI
    self.calibrator.set_temperature(self.nominal_temperature)

    # Pokretanje kalibratora 
    self.calibrator.set_output_on()       

  def thread_init(self):
    global thread
    # QThread ne dozvoljava prosledjivanje argumenata na worker = dva uzaludno potrosena dana - ALI moze preko konstruktora
    thread = Th(self.multimeter, self.calibrator, self.selector)
    thread.move_to_thread()
  
  

  
 


    











def not_blocking():
  print('not blocking')


# StartTime = time.time()

# def action():
#   pass
    # testiranje
    # print('{:.1f}s'.format(time.time() - StartTime))
    

# class setInterval:
#     def __init__(self, interval, action):
#         self.interval = interval
#         self.action = action
#         self.stopEvent = threading.Event()
#         thread = threading.Thread(target = self.__setInterval)
#         thread.start()

#     def __setInterval(self):
#         nextTime = time.time() + self.interval
#         while not self.stopEvent.wait(nextTime - time.time()):
#             nextTime += self.interval
#             print('fire')
#             self.action()

#     def cancel(self) :
#         self.stopEvent.set()

# run = setInterval(3, action)