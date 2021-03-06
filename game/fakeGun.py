#!/usr/bin/python

import argparse
import re
import socket
import sys
from threading import Thread, Lock
from time import time
import Queue

from PySide.QtCore import *
from PySide.QtGui import *

import proto

class TriggerButton(QPushButton):
  def __init__(self, serial, label, triggerDown, triggerUp, parent=None):
    super(TriggerButton, self).__init__(label, parent)
    self.serial = serial
    self.triggerDown = triggerDown
    self.triggerUp = triggerUp
    self.clicked.connect(self.trigger)

  def trigger(self):
    if self.triggerDown:
      self.serial.queueMessage(proto.TRIGGER.create())
    if self.triggerUp:
      self.serial.queueMessage(proto.TRIGGER_RELEASE.create())


class ShotButton(QPushButton):
  def __init__(self, serial, teamID, playerID, parent=None):
    super(ShotButton, self).__init__(str(teamID) + ", " + str(playerID), parent)
    self.serial = serial
    self.teamID = teamID
    self.playerID = playerID
    self.clicked.connect(self.shot)

  def shot(self):
    self.serial.queueMessage(proto.HIT.create(self.teamID, self.playerID, 3))


class MainWindow(QWidget):
  def __init__(self, serial, parent=None):
    super(MainWindow, self).__init__(parent)
    self.serial = serial

    self.setWindowTitle("BraidsTag Debugging Gun")
    layout = QVBoxLayout()
    hLayout = QHBoxLayout()

    hLayout.addWidget(TriggerButton(self.serial, "trigger", True, True))
    hLayout.addWidget(TriggerButton(self.serial, "trigger Down", True, False))
    hLayout.addWidget(TriggerButton(self.serial, "trigger Up", False, True))
    layout.addLayout(hLayout)

    for i in range(1,4):
      hLayout2 = QHBoxLayout()
      for j in range(1,4):
        hLayout2.addWidget(ShotButton(self.serial, i, j))
      layout.addLayout(hLayout2)

    self.setLayout(layout)


class SerialAdapter():
  readQueue = Queue.Queue()
  shouldStop = False

  def queueMessage(self, line):
    self.readQueue.put(line + "\n")

  def stop(self):
    self.shouldStop = True

  ## Writing

  def write(self, line):
    if line == "c\n":
      self.queueMessage("c")
    pass # We don't react to anything else the pi tells us yet

  ## Reading

  def __iter__(self):
    return self

  def next(self):
    while not self.shouldStop:
      try:
        return self.readQueue.get(True, 5)
      except Queue.Empty:
        continue
    
    # Stop the iteration
    raise StopIteration()

  def readline(self):
    return self.next()
    
  ## Misc

  def close(self):
    pass

class UIThread(Thread):
  serial = SerialAdapter()

  def run(self):
    # Create Qt application
    app = QApplication(sys.argv)

    mainWindow = MainWindow(self.serial)
    mainWindow.show()

    app.exec_()

    self.serial.stop()


def showUI():
  # Enter Qt main loop in a UI Thread
  uiThread = UIThread()
  uiThread.start()
  return uiThread.serial
