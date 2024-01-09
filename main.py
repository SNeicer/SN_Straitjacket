# SN-Straitjacket (Version v1.3) #
# GitHub: https://github.com/SNeicer/SN_Straitjacket #
# Discord: sneicer #
# EMail: b2jnz7hlw@mozmail.com #

import PyQt5.QtCore
from PyQt5 import QtWidgets, uic, QtGui
import sys
import os
import enum
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtWidgets import QWidget
import resource_rc
import tomlkit as tk
import psutil
import glob
import re
import yaml
from time import sleep
import multiprocessing
import shutil
import base64
from win32con import FILE_ATTRIBUTE_HIDDEN, FILE_ATTRIBUTE_NORMAL
from win32api import SetFileAttributes
import logging
import plyer
import winsound
import qdarktheme

# Implement plyer.platforms.win.notification as a hidden import

cur_app_version = 'release-v1.3' # Do not forget to update this one

class blockSubjectType(enum.Enum):
    app = 1
    website = 2

class mMulti(enum.Enum): # Millisecound Multiplyer
    secound = 1000
    minute = 60000
    hour = 3600000

class osValues(enum.Enum):
    hostsFile = r"C:\Windows\System32\drivers\etc\hosts"

# Utils Section

def util_writeConfigChanges():
    SetFileAttributes('config.toml', FILE_ATTRIBUTE_NORMAL)
    with open('config.toml', 'w') as configFile:
        tk.dump(config, configFile)
        SetFileAttributes('config.toml', FILE_ATTRIBUTE_HIDDEN)
    #logging.info("Config file updated")

def util_setupDefaultConfig():
    config = tk.document()

    config.add('is_advanced', False)

    cat_base = tk.table()
    cat_base.add('user_time', '01:00:00')
    cat_base.add('blocked_apps', [])
    cat_base.add('blocked_websites', [])
    cat_base.add('app_version', cur_app_version)
    cat_base.add('language', 'English')
    cat_base.add('theme', 0)

    cat_time_notif = tk.table()
    cat_time_notif.add('time_notif', False)
    cat_time_notif.add('notif_time', '00:01:00')
    cat_time_notif.add('notif_sound', False)
    cat_time_notif.add('open_app', False)

    cat_website_redir = tk.table()
    cat_website_redir.add('is_custom', False)
    cat_website_redir.add('custom_url', '127.0.0.1')

    cat_update_method = tk.table()
    cat_update_method.add('is_continuous', False)
    cat_update_method.add('refresh_rate', 2000) # In milliseconds

    cat_stop_method = tk.table()
    cat_stop_method.add('stop_type', 0)
    cat_stop_method.add('stop_password', 'None')

    # Adding tables to config
    config.add('BASE', cat_base)
    config.add('PREFERENCES_TIME_NOTIF', cat_time_notif)
    config.add('PREFERENCES_WEBSITE_REDIR', cat_website_redir)
    config.add('ADVANCED_UPDATE_METHOD', cat_update_method)
    config.add('ADVANCED_STOP_MODE', cat_stop_method)

    with open('config.toml', 'w') as configFile:
        tk.dump(config, configFile)
        SetFileAttributes('config.toml', FILE_ATTRIBUTE_HIDDEN)
    #logging.warning("Config file not found! Initializing a default one!")

def util_configCompatibilityCheck():
    if not ('app_version' in config['BASE']):
        config['BASE']['app_version'] = cur_app_version
    elif config['BASE']['app_version'] != cur_app_version:
        config['BASE']['app_version'] = cur_app_version

    if not ('language' in config['BASE']):
        config['BASE']['language'] = 'English'

    if not ('theme' in config['BASE']):
        config['BASE']['theme'] = 0

    util_writeConfigChanges()

def util_strToBool(value) -> bool:
    if value.lower() == 'true':
        return True
    else:
        return False

def util_convertToQTime(value):
    return PyQt5.QtCore.QTime.fromString(value, 'hh:mm:ss')

def util_convertToMsecs(value: str) -> int:
    timeFormated = value.split(':')
    timeFormated[0] = int(timeFormated[0])
    timeFormated[1] = int(timeFormated[1])
    timeFormated[2] = int(timeFormated[2])

    #Constucting a new time from pices to restrict dumb behaivor
    if timeFormated[2] > 99: # Seconds
        raise ValueError
    elif timeFormated[2] > 59:
        timeFormated[1] += 1
        timeFormated[2] -= 60

    if timeFormated[1] > 99: # Minutes
        raise ValueError
    elif timeFormated[1] > 59:
        timeFormated[0] += 1
        timeFormated[1] -= 60

    if timeFormated[0] > 99: # Hours
        raise ValueError

    # Converting time to milliseconds
    allMillTime = timeFormated[0] * mMulti.hour.value + timeFormated[1] * mMulti.minute.value + timeFormated[2] * mMulti.secound.value
    return allMillTime

def util_getTomlArrayAsList(value: tk.array):
    return list(value)

# Checking for having a config file

try:
    with open('config.toml', 'r') as configFile:
        config = tk.load(configFile)
    #logging.info("Existing config file loaded!")
except FileNotFoundError:
    util_setupDefaultConfig()
    with open('config.toml', 'r') as configFile:
        config = tk.load(configFile)

class multiprocessingBlocker():
    def __init__(self) -> None:
        self.blockList = list(config['BASE']['blocked_apps'])
        self.blockingProcces = multiprocessing.Process(target=self.blockApps, daemon=True)
        #logging.info("Multiprocessing blocker is initialized!")

    def stopBlockingProcess(self)-> None:
        if self.blockingProcces.is_alive():
            self.blockingProcces.terminate()
        #logging.warning("Multiprocessing blocker is stopped!")

    def updateBlockingProcess(self)-> None:
        self.stopBlockingProcess()
        self.blockList = list(config['BASE']['blocked_apps'])
        self.blockingProcces = multiprocessing.Process(target=self.blockApps)
        self.blockingProcces.start()
        #logging.warning("Multiprocessing blocker is updated!")

    def isBlockingContinuous(self) -> bool: # Check for 'is_continuous option'
        return bool(config['ADVANCED_UPDATE_METHOD']['is_continuous'])

    def blockApps(self) -> None:
        if not self.isBlockingContinuous():
            while True:
                for proc in psutil.process_iter():
                    if proc.name() in self.blockList:
                        proc.kill()
                        continue
                sleep(int(config['ADVANCED_UPDATE_METHOD']['refresh_rate'] / mMulti.secound.value))
        else:
            while True:
                for proc in psutil.process_iter(): # Some changes to locate this thingy
                    if proc.name() in self.blockList:
                        proc.kill()
                        continue

multiprocessing.freeze_support() # Freeze multiprocessing for blocker to prevent creating windows

# Custom exception hook
def snsj_exception_hook(exctype, value, traceback):
    logging.critical("Exception catched! Displaying...")
    logging.critical(f"{exctype}, {value}, {traceback}")

sys.excepthook = snsj_exception_hook

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename="log.log", filemode='w',
                        format="[%(asctime)s | %(funcName)s] %(levelname)s - %(message)s")
    from icoextract import IconExtractor, NoIconsAvailableError


class GetProcessesDialog(QtWidgets.QDialog):
    def __init__(self, loc_file, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi("Interfaces\\getProcessesDialog.ui", self)
        self.loc_file = loc_file
        self.setWindowTitle(self.loc_file['PROCESS_DIALOG']['title'])

        # Loading unknown icon for processes without icons
        self.icon_unknown = QtGui.QIcon()
        self.icon_unknown.addFile(u":/Icons/Resources/unknownIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Loading icons for buttons
        self.icon_select = QtGui.QIcon()
        self.icon_select.addFile(u":/Icons/Resources/checkIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_add = QtGui.QIcon()
        self.icon_add.addFile(u":/Icons/Resources/plusIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_back = QtGui.QIcon()
        self.icon_back.addFile(u":/Icons/Resources/backIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_refresh = QtGui.QIcon()
        self.icon_refresh.addFile(u":/Icons/Resources/refreshIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Adding those buttons
        self.addBBoxButtons()

        # Some thigs for process list
        self.system_proc_brush = QtGui.QBrush()
        self.system_proc_brush.setStyle(Qt.SolidPattern)
        self.system_proc_brush.setColor(Qt.blue)

        # Regex stuff
        self.regex_expression = re.compile(r"^[^\W][\w\d_. /:-]*$")

    # Adding buttons to button box
    def addBBoxButtons(self) -> None:
        # Creating buttons
        self.selectProcessesButton = QtWidgets.QPushButton()
        self.refreshButton = QtWidgets.QPushButton()
        self.directInputSelectionButton = QtWidgets.QPushButton()
        self.cancelSelectionButton = QtWidgets.QPushButton()

        # Adding icons to them
        self.refreshButton.setIcon(self.icon_refresh)
        self.directInputSelectionButton.setIcon(self.icon_add)
        self.selectProcessesButton.setIcon(self.icon_select)
        self.cancelSelectionButton.setIcon(self.icon_back)

        # Sizing buttons properly
        self.refreshButton.setIconSize(PyQt5.QtCore.QSize(32,32))
        self.directInputSelectionButton.setIconSize(PyQt5.QtCore.QSize(32,32))
        self.selectProcessesButton.setIconSize(PyQt5.QtCore.QSize(32,32))
        self.cancelSelectionButton.setIconSize(PyQt5.QtCore.QSize(32,32))

        # Adding buttons to the container and giving them a role
        self.bbox.addButton(self.selectProcessesButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.bbox.addButton(self.refreshButton, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.bbox.addButton(self.directInputSelectionButton, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.bbox.addButton(self.cancelSelectionButton, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)

        # Connecting buttons by using signals
        self.selectProcessesButton.clicked.connect(self.accept)
        self.refreshButton.clicked.connect(self.fillWithRunningProcesses)
        self.directInputSelectionButton.clicked.connect(self.selectFromName)
        self.cancelSelectionButton.clicked.connect(self.reject)

    def selectFromName(self) -> None:
        subjectName = QtWidgets.QInputDialog.getText(self, self.loc_file['BLOCKING']['app_title'],
                                                     self.loc_file['BLOCKING']['app_content'],
                                                     QtWidgets.QLineEdit.Normal, '')
        if subjectName[1]:
            if re.match(self.regex_expression, subjectName[0]): # yay regex!!
                new_block_item = QtWidgets.QListWidgetItem(subjectName[0] + f' ({self.loc_file["PROCESS_DIALOG"]["custom_item"]})')
                self.list_processes.insertItem(0, new_block_item)
                new_block_item.setSelected(True)
            else:
                info_box = QtWidgets.QMessageBox()
                info_box.warning(self, self.loc_file['PROCESS_DIALOG']['regex_warn_title'],
                                 self.loc_file['BASE']['regex_content_invalid'])

    def fillWithRunningProcesses(self) -> None:
        logging.warning('Filling process dialog with running executables')
        self.list_processes.clear()

        base_processes = []
        trusted_processes = []
        for proc in psutil.process_iter(): # Some changes to locate this thingy
            try:
                # Getting a process
                if proc.exe() != "" and proc.exe() != "Registry":
                    proc_item = QtWidgets.QListWidgetItem(f"{proc.name()} ({proc.exe()})")
                else:
                    continue

                # Getting an icon
                try:
                    extracted_icon = IconExtractor(proc.exe())
                    exe_icon = extracted_icon.get_icon()
                    exe_icon.seek(0) # Otherwise it will return b''. Which means - nothing
                    if exe_icon != b'': # Double check, just to be sure...
                        new_pixmap = QtGui.QPixmap()
                        new_pixmap.loadFromData(exe_icon.read())
                        new_icon = QtGui.QIcon()
                        new_icon.addPixmap(new_pixmap)
                        proc_item.setIcon(new_icon)
                    else:
                        proc_item.setIcon(self.icon_unknown)
                except (NoIconsAvailableError, FileNotFoundError):
                    logging.info(f"No icons found for process: {proc.name()}")
                    proc_item.setIcon(self.icon_unknown)

                # If situated in a system folder, make the process trusted
                if "C:\\Windows\\System32\\" in proc.exe():
                    proc_item.setForeground(self.system_proc_brush)
                    trusted_processes.append(proc_item)
                else:
                    base_processes.append(proc_item)

            except psutil.AccessDenied:
                logging.warning('Some app denied access!')
                continue

        # Filling with base processes
        for base_proc in base_processes:
            self.list_processes.addItem(base_proc)
        self.list_processes.sortItems()

        # Add trusted to the bottom
        for trusted_proc in trusted_processes:
            self.list_processes.addItem(trusted_proc)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        uic.loadUi("Interfaces\\mainWindowIconsV2.ui", self)
        util_configCompatibilityCheck()
        self.loadLocalizationFile()
        self.applyLocalizationToUi()
        self.updateAvalibleLanguages()
        self.show()
        self.getProcDialog = GetProcessesDialog(self.loc_file, self)
        self.info_box = QtWidgets.QMessageBox()
        self.updateListButtonStates()
        self.mainTimer = PyQt5.QtCore.QTimer() # Setting up main timer
        self.mainTimer.setTimerType(PyQt5.QtCore.Qt.VeryCoarseTimer) # Cutting all milliseconds...
        self.graphicalCountdownTimer = PyQt5.QtCore.QTimer();
        self.loadConfigSettings()
        self.updateAppBlockedList(blockSubjectType.app)
        self.updateAppBlockedList(blockSubjectType.website)
        self.blockManager = multiprocessingBlocker()
        self.updateButtonIcons()
        self.isNotificationPlayed = False # For canceling multiple activations at once
        #self.updateTheme()

        # Regex stuff
        self.regex_expression = re.compile(r"^[^\W][\w\d_. /:-]*$")

        # Some cosmetic stuff for main window and info box
        windowIcon = QtGui.QIcon()
        windowIcon.addFile(u":/Icons/Resources/setTimeIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_themeDark = QtGui.QIcon()
        self.icon_themeDark.addFile(u":/Icons/Resources/moonIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_themeLight = QtGui.QIcon()
        self.icon_themeLight.addFile(u":/Icons/Resources/sunIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(windowIcon)
        self.info_box.setWindowIcon(windowIcon)
        self.setWindowTitle(f'SN_Straitjacket - {cur_app_version}')

        # Setting up button connections
        #self.btn_addApp.clicked.connect(lambda: self.addBlockedSubject(blockSubjectType.app))
        self.btn_addApp.clicked.connect(self.blockAppsFromDialog)
        self.btn_directAdd.clicked.connect(lambda: self.addBlockedSubject(blockSubjectType.app))
        self.btn_addWebsite.clicked.connect(lambda: self.addBlockedSubject(blockSubjectType.website))

        self.btn_remApp.clicked.connect(lambda: self.removeBlockedSubject(blockSubjectType.app))
        self.btn_remWebsite.clicked.connect(lambda: self.removeBlockedSubject(blockSubjectType.website))

        self.btn_editApp.clicked.connect(lambda: self.editBlockedSubject(blockSubjectType.app))
        self.btn_editWebsite.clicked.connect(lambda: self.editBlockedSubject(blockSubjectType.website))

        self.btn_timerSetup.clicked.connect(self.userSetupTimer)
        self.btn_timerSwitch.clicked.connect(self.startStopTimer)

        self.btn_timerFullStop.clicked.connect(self.fullStopTimer)

        self.gbox_advanced.toggled.connect(self.updateGroupStates)

        # Theme btn
        self.btn_changeTheme.clicked.connect(self.changeTheme)

        # Updating action buttons in apps and websites tab
        self.list_blockedApps.currentRowChanged.connect(self.updateListButtonStates)
        self.list_blockedWebsites.currentRowChanged.connect(self.updateListButtonStates)

        self.btn_clearApps.clicked.connect(lambda: self.clearBlockedSubjectList(blockSubjectType.app))
        self.btn_clearWebsites.clicked.connect(lambda: self.clearBlockedSubjectList(blockSubjectType.website))

        # Timers
        self.mainTimer.timeout.connect(self.mainTimerTimeout)

        # Updating group boxes in settings after making changes to rbtn's
        self.rbtn_customRedirect.toggled.connect(self.updateGroupStates)
        self.rbtn_continuousUpdate.toggled.connect(self.updateGroupStates)
        self.combox_stopType.currentIndexChanged.connect(self.updateGroupStates)

        # Making settings buttons actually do something
        self.btn_stopPasswordSet.clicked.connect(self.setCustomStopPassword)
        self.btn_setCustomRedirect.clicked.connect(self.setCustomRedirect)
        self.btn_resetCustomRedirect.clicked.connect(self.resetCustomRedirect)

        # Connecting refresh rate slider
        self.slider_refreshRate.valueChanged.connect(self.updateRefreshRate)

        # Connecting time notification
        self.btn_setNotifTime.clicked.connect(self.updateNotificationTime)
        self.gbox_timeNotification.clicked.connect(self.updateGroupStates)
        self.cbox_playNotifSound.clicked.connect(self.updateGroupStates)
        self.cbox_openUiAfterNotif.clicked.connect(self.updateGroupStates)

        # Language change
        self.combox_language.currentIndexChanged.connect(self.onLocalizationChanged)

        # Logging
        logging.info("MainWindow initialized!")

    # Base functions

    def resetSettings(self) -> None: # Defaults everything
        util_setupDefaultConfig()
        logging.warning("Reset settings is called! Defaulting everything...")

    def loadConfigSettings(self) -> None: # Loads and applies all config settings
        # Converting time nortification time string to QTime for future use
        configTime = util_convertToQTime(config['PREFERENCES_TIME_NOTIF']['notif_time'])

        # Base
        self.lable_time.setText(config['BASE']['user_time'])
        self.mainTimer.setInterval(util_convertToMsecs(config['BASE']['user_time']))

        # PREFERENCES_TIME_NOTIF
        self.gbox_timeNotification.setChecked(config['PREFERENCES_TIME_NOTIF']['time_notif'])
        self.cbox_playNotifSound.setChecked(config['PREFERENCES_TIME_NOTIF']['notif_sound'])
        self.cbox_openUiAfterNotif.setChecked(config['PREFERENCES_TIME_NOTIF']['open_app'])
        self.labl_curNotification.setText(self.loc_file['NOTIFICATION']['notifset_text'].format(
            configTime.hour(), self.loc_file['BASE']['hour'],
            configTime.minute(), self.loc_file['BASE']['minute'],
            configTime.second(), self.loc_file['BASE']['second']
        ))
        self.tedit_notificationTime.setTime(configTime)

        # PREFERENCES_WEBSITE_REDIR
        if config['PREFERENCES_WEBSITE_REDIR']['is_custom']:
            self.gbox_customRedirect.setEnabled(True)
            self.rbtn_customRedirect.setChecked(True)
            self.rbtn_defaultRedirect.setChecked(False)
        else:
            self.rbtn_defaultRedirect.setChecked(True)
            self.gbox_customRedirect.setEnabled(False)
            self.rbtn_customRedirect.setChecked(False)
        self.ledit_customRedirect.setText(config['PREFERENCES_WEBSITE_REDIR']['custom_url'])

        # ADVANCED
        self.gbox_advanced.setChecked(config['is_advanced'])

        # ADVANCED_UPDATE_METHOD
        if config['ADVANCED_UPDATE_METHOD']['is_continuous']:
            self.rbtn_continuousUpdate.setChecked(True)
            self.rbtn_fixedRefreshRate.setChecked(False)
            self.gbox_adv_refreshRate.setEnabled(False)
        else:
            self.rbtn_fixedRefreshRate.setChecked(True)
            self.rbtn_continuousUpdate.setChecked(False)
            self.gbox_adv_refreshRate.setEnabled(True)
        self.slider_refreshRate.setValue(int(config['ADVANCED_UPDATE_METHOD']['refresh_rate']))
        self.labl_refreshRateText.setText(f'{round(self.slider_refreshRate.value()/mMulti.secound.value, 1)} {self.loc_file["BASE"]["second_long"]}')

        # ADVANCED_STOP_MODE
        match (int(config['ADVANCED_STOP_MODE']['stop_type'])):
            case 0:
                self.combox_stopType.setCurrentIndex(0)
                self.gbox_passwordStop.setEnabled(False)
            case 1:
                self.combox_stopType.setCurrentIndex(1)
                self.gbox_passwordStop.setEnabled(False)
            case 2:
                self.combox_stopType.setCurrentIndex(2)
                self.gbox_passwordStop.setEnabled(True)
            case _: # Copying free stop option
                self.combox_stopType.setCurrentIndex(0)
                self.gbox_passwordStop.setEnabled(False)
        logging.info("Config loaded successfully!")

    # Multiprocessing operations

    def updateBlockingProcces(self) -> None: # Updates a blocking multiprocess
        self.blockManager.updateBlockingProcess()

    def stopBlockingProcces(self) -> None: # Stops a blocking multiprocess
        self.blockManager.stopBlockingProcess()

    # Main timer operations

    def userSetupTimer(self) -> None: # Function for setting up a timer by user input
        userTime = QtWidgets.QInputDialog.getText(self, self.loc_file['WIDGETS']['usertime_title'],
                                                  self.loc_file['WIDGETS']['usertime_content'],
                                                  QtWidgets.QLineEdit.Normal, config['BASE']['user_time'])
        if userTime[1]:
            try:
                allMillTime = util_convertToMsecs(userTime[0])
            except ValueError:
                self.info_box.warning(self, self.loc_file['WIDGETS']['usertime_warning_title'],
                                      self.loc_file['WIDGETS']['usertime_warning_content'])
                logging.error("User wrote some gibberish!")
                return 'Wrong format error'
            self.updateConfigTime(userTime[0])
            self.fullStopTimer()
        else:
            return 'Action canceled'
        logging.warning("User changed timer interval!")

    def updateTimerLabel(self) -> None: # Updates timer label
        time = 0 # Storing a proper time value depending on mainTimer activation
        if self.mainTimer.isActive():
            time = self.mainTimer.remainingTime()
        else:
            time = self.mainTimer.interval()

        self.lable_time.setText(PyQt5.QtCore.QTime(0,0,0).addMSecs(time).toString('hh:mm:ss'))
        self.launchTimerLabelUpdateRoutine()
        if config['PREFERENCES_TIME_NOTIF']['time_notif'] and not self.isNotificationPlayed:
            self.checkForNotification()

    def startStopTimer(self) -> None: # Manual startup and stoppage of a timer
        if not self.mainTimer.isActive():
            self.mainTimer.start()
            self.updateBlockingProcces()
            self.blockWebsites()
            self.lockSettingsChange()
            self.updateButtonIcons()
            self.forceStopButtonActivation()
            self.launchTimerLabelUpdateRoutine()
            logging.warning('Main timer is manualy activated!')
        elif self.mainTimer.isActive():

            if config['ADVANCED_STOP_MODE']['stop_type'] == 2:
                passGranted = self.askStopPassword(self.loc_file['WIDGETS']['pass_ask_content_pause'])
                if not passGranted:
                    return False

            if config['ADVANCED_STOP_MODE']['stop_type'] == 1: # Fool protection
                return False

            remainingTime = self.mainTimer.remainingTime()
            self.mainTimer.stop()
            self.mainTimer.setInterval(remainingTime)
            self.updateTimerLabel()
            self.stopBlockingProcces()
            self.unblockWebsites()
            self.unlockSettingsChange()
            self.updateButtonIcons()
            self.isNotificationPlayed = False
            logging.warning('Main timer is manualy deactivated!')
        else:
            logging.critical('This should not happen... but meh, passing by...')

    def mainTimerTimeout(self) -> None: # Natural timeout of a timer
        self.mainTimer.stop()
        self.mainTimer.setInterval(util_convertToMsecs(config['BASE']['user_time']))
        self.updateTimerLabel()
        self.stopBlockingProcces()
        self.unblockWebsites()
        self.unlockSettingsChange()
        self.updateButtonIcons()
        self.isNotificationPlayed = False
        logging.warning('Main timer timeout!')

    def fullStopTimer(self) -> None: # Manual full stoppage of a timer
        if config['ADVANCED_STOP_MODE']['stop_type'] == 2:
            passGranted = self.askStopPassword(self.loc_file['WIDGETS']['pass_ask_content_fullstop'])
            if passGranted:
                self.mainTimerTimeout()
                logging.warning('Main timer is manualy full stoped!')
            else:
                self.info_box.warning(self, self.loc_file['WIDGETS']['wrongpass_warning_title'], self.loc_file['WIDGETS']['wrongpass_warning_content'])
        else:
            self.mainTimerTimeout()
            logging.warning('Main timer is manualy full stoped!')

    def updateConfigTime(self, time: str) -> None:
        logging.info("Updating user_time in config...")
        config['BASE']['user_time'] = time
        util_writeConfigChanges()

    # Countdown label

    def launchTimerLabelUpdateRoutine(self) -> None:
        if self.mainTimer.isActive():
            self.graphicalCountdownTimer.singleShot(10, self.updateTimerLabel) # Updating a label every 10ms (To be less cpu hungry)

    # Overall Ui operations

    def updateButtonIcons(self) -> None: # Updates regarding btn icons

        icon_startTimer = QtGui.QIcon()
        icon_startTimer.addFile(u":/Icons/Resources/startIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        icon_pauseTimer = QtGui.QIcon()
        icon_pauseTimer.addFile(u":/Icons/Resources/pauseIcon.png", PyQt5.QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        if self.mainTimer.isActive():
            self.btn_timerSwitch.setIcon(icon_pauseTimer)
            self.btn_timerSwitch.setIconSize(PyQt5.QtCore.QSize(32, 32))
            self.btn_timerSetup.setEnabled(False)
            if config['ADVANCED_STOP_MODE']['stop_type'] == 1:
                self.btn_timerSwitch.setEnabled(False)
            else:
                self.btn_timerSwitch.setEnabled(True)
        else:
            self.btn_timerSwitch.setIcon(icon_startTimer)
            self.btn_timerSwitch.setIconSize(PyQt5.QtCore.QSize(32, 32))
            self.btn_timerSwitch.setEnabled(True)
            self.btn_timerSetup.setEnabled(True)

        if self.mainTimer.interval() != util_convertToMsecs(config['BASE']['user_time']):
            if config['ADVANCED_STOP_MODE']['stop_type'] == 1:
                self.btn_timerFullStop.setEnabled(False)
            else:
                self.btn_timerFullStop.setEnabled(True)
        else:
            self.btn_timerFullStop.setEnabled(False)
        logging.info("Button icons and functionality is updated!")

    def forceStopButtonActivation(self) -> None: # Forces stop button to activate
        if config['ADVANCED_STOP_MODE']['stop_type'] == 1:
            self.btn_timerFullStop.setEnabled(False)
        else:
            logging.info("Stop button is forced to be turned on...")
            self.btn_timerFullStop.setEnabled(True)

    def updateGroupStates(self) -> None: # Enables or disables certain ui groups after making a change
        # Update them in config
        config['PREFERENCES_WEBSITE_REDIR']['is_custom'] = self.rbtn_customRedirect.isChecked()
        config['ADVANCED_UPDATE_METHOD']['is_continuous'] = self.rbtn_continuousUpdate.isChecked()
        config['PREFERENCES_TIME_NOTIF']['time_notif'] = self.gbox_timeNotification.isChecked()
        config['PREFERENCES_TIME_NOTIF']['notif_sound'] = self.cbox_playNotifSound.isChecked()
        config['PREFERENCES_TIME_NOTIF']['open_app'] = self.cbox_openUiAfterNotif.isChecked()
        config['is_advanced'] = self.gbox_advanced.isChecked()

        if config['ADVANCED_STOP_MODE']['stop_type'] != self.combox_stopType.currentIndex():
            if config['ADVANCED_STOP_MODE']['stop_type'] == 2:
                passGranted = self.askStopPassword(self.loc_file['WIDGETS']['pass_ask_content_changestop'])
                if not passGranted:
                    self.info_box.warning(self, self.loc_file['WIDGETS']['wrongpass_warning_title'], self.loc_file['WIDGETS']['wrongpass_warning_content'])
                    self.combox_stopType.setCurrentIndex(2)
                else:
                    config['ADVANCED_STOP_MODE']['stop_type'] = self.combox_stopType.currentIndex()
            else:
                config['ADVANCED_STOP_MODE']['stop_type'] = self.combox_stopType.currentIndex()
        util_writeConfigChanges()

        # Update them in ui
        self.gbox_customRedirect.setEnabled(self.rbtn_customRedirect.isChecked())
        if self.combox_stopType.currentIndex() == 2:
            self.gbox_passwordStop.setEnabled(True)
        else:
            self.gbox_passwordStop.setEnabled(False)
        self.gbox_adv_refreshRate.setEnabled(self.rbtn_fixedRefreshRate.isChecked())
        self.ledit_customRedirect.setText(config['PREFERENCES_WEBSITE_REDIR']['custom_url'])

        if config['ADVANCED_STOP_MODE']['stop_password'] == "":
            self.gbox_passwordStop.setTitle(self.loc_file['UI']['gbox_passwordStop_na'])
        else:
            self.gbox_passwordStop.setTitle(self.loc_file['UI']['gbox_passwordStop_set'])

        logging.warning("Group states are updated!")

    def lockSettingsChange(self) -> None: # Locks all settings in place and prevents making a change
        self.tab_settings.setEnabled(False)
        self.tab_apps.setEnabled(False)
        self.tab_websites.setEnabled(False)
        logging.warning("Settings changes are disabled!")

    def unlockSettingsChange(self) -> None: # Unlocks all settings
        self.tab_settings.setEnabled(True)
        self.tab_apps.setEnabled(True)
        self.tab_websites.setEnabled(True)
        logging.warning("Settings changes are enabled!")

    # Custom redirect

    def setCustomRedirect(self) -> None: # On clicking custom redirect set button
        if self.ledit_customRedirect.text() != '':
            config['PREFERENCES_WEBSITE_REDIR']['custom_url'] = self.ledit_customRedirect.text()
            util_writeConfigChanges()
            self.info_box.information(self, self.loc_file['WIDGET']['customredir_title'], self.loc_file['WIDGET']['customredir_content'].format(self.ledit_customRedirect.text()))
            self.updateGroupStates()
        else:
            self.info_box.warning(self, self.loc_file['WIDGET']['customredir_warning_title'], self.loc_file['WIDGET']['customredir_warning_content'])
            self.ledit_customRedirect.setText(config['PREFERENCES_WEBSITE_REDIR']['custom_url'])
        logging.warning("Custom redirect is set")

    def resetCustomRedirect(self) -> None: # On clicking custom redirect reset button
        self.ledit_customRedirect.setText('127.0.0.1')
        config['PREFERENCES_WEBSITE_REDIR']['custom_url'] = self.ledit_customRedirect.text()
        util_writeConfigChanges()
        self.info_box.information(self, self.loc_file['WIDGET']['customredir_restore_title'] , self.loc_file['WIDGET']['customredir_restore_content'])
        self.updateGroupStates()
        logging.warning("Custom redirect reset")

    # Refresh rate

    def updateRefreshRate(self) -> None: # Updates refresh rate in config and then in gui
        config['ADVANCED_UPDATE_METHOD']['refresh_rate'] = self.slider_refreshRate.value()
        util_writeConfigChanges()
        self.updateGUIRefreshRateLabel()
        logging.info("Blocker refresh rate is updated")

    def updateGUIRefreshRateLabel(self) -> None: # Updates refresh rate label in gui thru config
        self.labl_refreshRateText.setText(str(round(config['ADVANCED_UPDATE_METHOD']['refresh_rate']/mMulti.secound.value, 1)) + f" {self.loc_file['BASE']['second_long']}")

    # Stop password

    def setCustomStopPassword(self) -> None:
        if self.ledit_stopPassword.text() != '':
            if config['ADVANCED_STOP_MODE']['stop_password'] != "None" and config['ADVANCED_STOP_MODE']['stop_type'] == 2:
                passGranted = self.askStopPassword(self.loc_file['WIDGETS']['pass_ask_content_old'])
                if not passGranted:
                    self.info_box.warning(self, self.loc_file['WIDGETS']['wrongpass_warning_title'], self.loc_file['WIDGETS']['wrongpass_warning_content'])
                    return False
            encodedPass = self.ledit_stopPassword.text().encode('utf-8')
            hashedPass = base64.b64encode(encodedPass)
            config['ADVANCED_STOP_MODE']['stop_password'] = str(hashedPass)
            util_writeConfigChanges()
            self.info_box.information(self, self.loc_file['WIDGETS']['pass_set_title'], self.loc_file['WIDGETS']['pass_set_content'])
            self.updateGroupStates()
            logging.warning("Stop password is set!")
        else:
            self.info_box.warning(self, self.loc_file['WIDGETS']['pass_set_warning_title'], self.loc_file['WIDGETS']['pass_set_warning_content'])

    def askStopPassword(self, stopPassReasonText: str) -> bool:
        logging.warning("Asking a stop password...")
        if config['ADVANCED_STOP_MODE']['stop_password'] != "None":
            userPass = QtWidgets.QInputDialog.getText(self, self.loc_file['WIDGETS']['pass_ask_title'],
                                                            stopPassReasonText,
                                                            QtWidgets.QLineEdit.Normal,
                                                            '')
            if userPass[1]:
                encryptedConfigPass = bytes(config['ADVANCED_STOP_MODE']['stop_password'], 'utf-8').decode()
                decodedPassword = base64.b64decode(encryptedConfigPass.strip("'b")).decode('utf-8')
                if userPass[0] == decodedPassword:
                    logging.warning("Stop password is entered correctly, granting access...")
                    return True
                else:
                    logging.warning("Stop password is entered incorrectly, denying access...")
                    return False
            else:
                logging.warning("Stop password window is closed!")
                return False
        else:
            logging.warning("Stop password is empty! Granting access")
            return True

    # Block list operations

    def updateConfigBlockedLists(self, type: blockSubjectType) -> None: # Updates only config block lists with new info on blocked subjects
        match (type):
            case blockSubjectType.app:
                blockedApps = []
                if self.list_blockedApps.count() > 0:
                    for i in range(self.list_blockedApps.count()):
                        blockedApps.append(self.list_blockedApps.item(i).text())
                else:
                    blockedApps = []
                config['BASE']['blocked_apps'] = blockedApps
                logging.warning("Config block list for apps is pending for update!")
            case blockSubjectType.website:
                blockedWebsites = []
                if self.list_blockedWebsites.count() > 0:
                    for i in range(self.list_blockedWebsites.count()):
                        blockedWebsites.append(self.list_blockedWebsites.item(i).text())
                else:
                    blockedWebsites = []
                config['BASE']['blocked_websites'] = blockedWebsites
                logging.warning("Config block list for websites is pending for update!")
            case _:
                logging.critical("Why... idk... passing by...")

        util_writeConfigChanges()

    def updateAppBlockedList(self, type: blockSubjectType) -> None: # Updates only app block lists with config values
        match type:
            case blockSubjectType.app:
                self.list_blockedApps.clear()
                self.list_blockedApps.addItems(config['BASE']['blocked_apps'])
                logging.info("UI side of app block list is updated")
            case blockSubjectType.website:
                self.list_blockedWebsites.clear()
                self.list_blockedWebsites.addItems(config['BASE']['blocked_websites'])
                logging.info("UI side of website block list is updated")
            case _:
                pass

    def updateListButtonStates(self) -> None: # Enables/Disables buttons depending on selected items in lists
        if self.list_blockedApps.currentItem() == None:
            self.btn_remApp.setEnabled(False)
            self.btn_editApp.setEnabled(False)
        else:
            self.btn_remApp.setEnabled(True)
            self.btn_editApp.setEnabled(True)

        if self.list_blockedWebsites.currentItem() == None:
            self.btn_remWebsite.setEnabled(False)
            self.btn_editWebsite.setEnabled(False)
        else:
            self.btn_remWebsite.setEnabled(True)
            self.btn_editWebsite.setEnabled(True)

        self.btn_clearApps.setEnabled(bool(self.list_blockedApps.count()))
        self.btn_clearWebsites.setEnabled(bool(self.list_blockedWebsites.count()))
        logging.warning("Buttons for ui lists are updated!")

    def addBlockedSubject(self, type: blockSubjectType) -> None: # Speaks for itself
        logging.warning("User is adding a new blocking subject!")
        match (type):
            case blockSubjectType.app:
                subjectName = QtWidgets.QInputDialog.getText(self,
                                                             self.loc_file['BLOCKING']['app_title'],
                                                             self.loc_file['BLOCKING']['app_content'],
                                                             QtWidgets.QLineEdit.Normal, '')
                if subjectName[1]: # Check for canceling
                    if re.match(self.regex_expression, subjectName[0]): # Checking for validity
                        self.list_blockedApps.addItem(subjectName[0])
                        self.info_box.information(self, self.loc_file['BLOCKING']['app_title'],
                                             self.loc_file['BLOCKING']['app_added'].format(subjectName[0]))
                        self.updateConfigBlockedLists(blockSubjectType.app)
                        logging.warning(f"App '{subjectName[0]}' was added to app block list!")
                    else:
                        self.info_box.warning(self, self.loc_file['BLOCKING']['app_title'],
                                         self.loc_file['BASE']['regex_content_invalid'])
            case blockSubjectType.website:
                subjectName = QtWidgets.QInputDialog.getText(self,
                                                             self.loc_file['BLOCKING']['web_title'],
                                                             self.loc_file['BLOCKING']['web_content'],
                                                             QtWidgets.QLineEdit.Normal, '')
                if subjectName[1]: # Check for canceling
                    if re.match(self.regex_expression, subjectName[0]): # Checking for validity
                        self.list_blockedWebsites.addItem(subjectName[0])
                        self.info_box.information(self, self.loc_file['BLOCKING']['web_title'],
                                             self.loc_file['BLOCKING']['web_added'].format(subjectName[0]))
                        self.updateConfigBlockedLists(blockSubjectType.website)
                        logging.warning(f"Website '{subjectName[0]}' was added to website block list!")
                    else:
                        self.info_box.warning(self, self.loc_file['BLOCKING']['web_title'],
                                         self.loc_file['BASE']['regex_content_invalid'])
            case _:
                logging.critical("wha... well... doin nothing then...")

    def editBlockedSubject(self, type: blockSubjectType) -> None: # Speaks for itself
        logging.warning(f"User is editing a blocked subject! Type: {type}")
        match (type):
            case blockSubjectType.app:
                if self.list_blockedApps.currentItem() != None:
                    itemOldText = self.list_blockedApps.currentItem().text()
                    subjectChangedName = QtWidgets.QInputDialog.getText(self, self.loc_file['BLOCKING']['app_edit_title'],
                                                                        self.loc_file['BLOCKING']['app_edit_content'],
                                                                        QtWidgets.QLineEdit.Normal,
                                                                        itemOldText)
                if subjectChangedName[1]: # Check for canceling
                    if subjectChangedName[0] != '' and subjectChangedName[0][0] != '.':
                        self.list_blockedApps.currentItem().setText(subjectChangedName[0])
                        self.info_box.information(self, self.loc_file['BLOCKING']['app_edit_title'],
                                                  self.loc_file['BLOCKING']['app_edit_done'].format(itemOldText, subjectChangedName[0]))
                        self.updateConfigBlockedLists(blockSubjectType.app)
                        logging.warning(f"Subject '{itemOldText}' is renamed to '{subjectChangedName[0]}'!")
                    else:
                        self.info_box.warning(self, self.loc_file['BLOCKING']['app_edit_title'],
                                              self.loc_file['BLOCKING']['app_edit_nofill'])
                        logging.error("New subject name is invalid...")
            case blockSubjectType.website:
                if self.list_blockedWebsites.currentItem() != None:
                    itemOldText = self.list_blockedWebsites.currentItem().text()
                    subjectChangedName = QtWidgets.QInputDialog.getText(self, self.loc_file['BLOCKING']['web_edit_title'],
                                                                        self.loc_file['BLOCKING']['web_edit_content'],
                                                                        QtWidgets.QLineEdit.Normal,
                                                                        itemOldText)
                if subjectChangedName[1]: # Check for canceling
                    if subjectChangedName[0] != '' and subjectChangedName[0][0] != '.':
                        self.list_blockedWebsites.currentItem().setText(subjectChangedName[0])
                        self.info_box.information(self, self.loc_file['BLOCKING']['web_edit_title'],
                                                  self.loc_file['BLOCKING']['web_edit_done'].format(itemOldText, subjectChangedName[0]))
                        self.updateConfigBlockedLists(blockSubjectType.website)
                        logging.error(f"Website adress of '{itemOldText}' changed to '{subjectChangedName[0]}'!")
                    else:
                        self.info_box.warning(self, self.loc_file['BLOCKING']['web_edit_title'],
                                              self.loc_file['BLOCKING']['web_edit_nofill'])
                        logging.error("New subject adress is invalid...")
            case _:
                logging.critical("edit go wild... moving on...")

    def removeBlockedSubject(self, type: blockSubjectType) -> None: # Speaks for itself
        logging.warning(f"User is trying to remove a subject! Type: {type}")
        match (type):
            case blockSubjectType.app:
                if self.list_blockedApps.currentItem() != None:
                    user_agree = self.info_box.question(self, self.loc_file['BLOCKING']['app_rem_title'],
                                                        self.loc_file['BLOCKING']['app_rem_content'].format(self.list_blockedApps.currentItem().text()),
                                                        self.info_box.Yes | self.info_box.No)
                    if user_agree == self.info_box.Yes:
                        takenItem = self.list_blockedApps.takeItem(self.list_blockedApps.currentRow())
                        del takenItem
                        self.updateConfigBlockedLists(blockSubjectType.app)
                        logging.warning("Blocking subject is removed!")
            case blockSubjectType.website:
                if self.list_blockedWebsites.currentItem() != None:
                    user_agree = self.info_box.question(self, self.loc_file['BLOCKING']['web_rem_title'],
                                                        self.loc_file['BLOCKING']['web_rem_content'].format(self.list_blockedWebsites.currentItem().text()),
                                                        self.info_box.Yes | self.info_box.No)
                    if user_agree == self.info_box.Yes:
                        takenItem = self.list_blockedWebsites.takeItem(self.list_blockedWebsites.currentRow())
                        del takenItem
                        self.updateConfigBlockedLists(blockSubjectType.website)
                        logging.warning("Blocking subject is removed!")
            case _:
                logging.warning("removing go wild... moving on...")

    def clearBlockedSubjectList(self, type: blockSubjectType) -> None:
        logging.critical(f"User is trying to clear blocked list! Type: {type}")
        match (type):
            case blockSubjectType.app:
                listCount = self.list_blockedApps.count()
                userSure = self.info_box.question(self, self.loc_file['BLOCKING']['app_clear_title'],
                                                  self.loc_file['BLOCKING']['app_clear_ask_content'],
                                                  self.info_box.No | self.info_box.Yes)
                if userSure == self.info_box.Yes:
                    self.list_blockedApps.clear()
                    self.info_box.information(self, self.loc_file['BLOCKING']['app_clear_title'],
                                              self.loc_file['BLOCKING']['app_clear_content'].format(listCount))
                    self.updateConfigBlockedLists(blockSubjectType.app)
                    logging.critical("List is cleared!")
            case blockSubjectType.website:
                listCount = self.list_blockedWebsites.count()
                userSure = self.info_box.question(self, self.loc_file['BLOCKING']['web_clear_title'],
                                                  self.loc_file['BLOCKING']['web_clear_ask_content'],
                                                  self.info_box.No | self.info_box.Yes)
                if userSure == self.info_box.Yes:
                    self.list_blockedWebsites.clear()
                    self.info_box.information(self, self.loc_file['BLOCKING']['web_clear_title'],
                                              self.loc_file['BLOCKING']['web_clear_content'].format(listCount))
                    self.updateConfigBlockedLists(blockSubjectType.website)
                    logging.critical("List is cleared!")
            case _:
                logging.critical("clearing go wild... moving on...")
        self.updateListButtonStates()

    def blockAppsFromDialog(self) -> None:
        self.getProcDialog.fillWithRunningProcesses()
        if self.getProcDialog.exec():
            selectedProcessItems = self.getProcDialog.list_processes.selectedItems()
            selectedProcesses = []
            for process in selectedProcessItems:
                processRealName = process.text().split(" (")[0]
                selectedProcesses.append(processRealName)
                selectedProcesses = list(dict.fromkeys(selectedProcesses)) # To avoid duplicates
            logging.warning(f'User selection: {selectedProcesses}')
            for blockedSelection in selectedProcesses:
                if not blockedSelection in config['BASE']['blocked_apps']:
                    self.list_blockedApps.addItem(blockedSelection)
                else:
                    logging.warning(f'Selected item "{blockedSelection}" already in a block list! Skipping...')
            self.updateConfigBlockedLists(blockSubjectType.app)
            logging.warning('Selected items are added to the block list!')
            self.info_box.information(self, self.loc_file['BLOCKING']['app_dialog_title'],
                                      self.loc_file['BLOCKING']['app_dialog_content'])
        else:
            logging.warning('User canceled selection!')

    # Localization operations

    def loadLocalizationFile(self) -> None:
        try:
            logging.info("Loading localization from config...")
            with open(f".\\Localization\\{config['BASE']['language']}.yml", "r", encoding='utf-8') as loc_file:
                self.loc_file = yaml.safe_load(loc_file)
            logging.info("Localization loaded!")
        except FileNotFoundError:
            logging.critical("Localization file not found! Loading English.toml instead!")
            config['BASE']['language'] = "English"
            util_writeConfigChanges()
            with open(f".\\Localization\\English.yml", "r", encoding='utf-8') as loc_file:
                self.loc_file = yaml.safe_load(loc_file)
            self.info_box.warning(self, 'Loading localization', 'Localization file not found! Using default english instead!')
            logging.warning("Localization defaulted to English!")

    def applyLocalizationToUi(self) -> None:
        self.labl_language.setText(self.loc_file['UI']['labl_language'])
        self.gbox_timeNotification.setTitle(self.loc_file['UI']['gbox_timeNotification'])
        self.gbox_webRedirect.setTitle(self.loc_file['UI']['gbox_webRedirect'])
        self.btn_setNotifTime.setText(self.loc_file['UI']['btn_setNotifTime'])
        self.cbox_playNotifSound.setText(self.loc_file['UI']['cbox_playNotifSound'])
        self.cbox_openUiAfterNotif.setText(self.loc_file['UI']['cbox_openUiAfterNotif'])
        self.rbtn_defaultRedirect.setText(self.loc_file['UI']['rbtn_defaultRedirect'])
        self.rbtn_customRedirect.setText(self.loc_file['UI']['rbtn_customRedirect'])
        self.gbox_customRedirect.setTitle(self.loc_file['UI']['gbox_customRedirect'])
        self.btn_resetCustomRedirect.setText(self.loc_file['UI']['btn_resetCustomRedirect'])
        self.btn_setCustomRedirect.setText(self.loc_file['UI']['btn_setCustomRedirect'])
        self.gbox_advanced.setTitle(self.loc_file['UI']['gbox_advanced'])
        self.gbox_adv_updateMethod.setTitle(self.loc_file['UI']['gbox_adv_updateMethod'])
        self.rbtn_continuousUpdate.setText(self.loc_file['UI']['rbtn_continuousUpdate'])
        self.rbtn_fixedRefreshRate.setText(self.loc_file['UI']['rbtn_fixedRefreshRate'])
        self.gbox_adv_refreshRate.setTitle(self.loc_file['UI']['gbox_adv_refreshRate'])
        self.updateGUIRefreshRateLabel()
        self.gbox_adv_stopMode.setTitle(self.loc_file['UI']['gbox_adv_stopMode'])
        self.labl_stopType.setText(self.loc_file['UI']['labl_stopType'])
        self.btn_stopPasswordSet.setText(self.loc_file['UI']['btn_stopPasswordSet'])

        # Stop mode combobox
        self.combox_stopType.setItemText(0, self.loc_file['UI']['combox_stopType_free'])
        self.combox_stopType.setItemText(1, self.loc_file['UI']['combox_stopType_strict'])
        self.combox_stopType.setItemText(2, self.loc_file['UI']['combox_stopType_password'])

        # Tabs
        self.tabWidget.setTabText(0, self.loc_file['TABS']['timer'])
        self.tabWidget.setTabText(1, self.loc_file['TABS']['apps'])
        self.tabWidget.setTabText(2, self.loc_file['TABS']['websites'])
        self.tabWidget.setTabText(3, self.loc_file['TABS']['preferences'])
        self.tabWidget.setTabText(4, self.loc_file['TABS']['credits'])

        # Time notification fix (Garbage not a fix, look at line loadConfigSettings... FIX THAT)
        self.tedit_notificationTime.setTime(QTime.fromString(config['PREFERENCES_TIME_NOTIF']['notif_time'], 'hh:mm:ss'))
        self.updateTimeNotificationText(self.tedit_notificationTime.time())

        # Password gbox
        self.updateGroupStates()

    def onLocalizationChanged(self) -> None:
        new_language = self.combox_language.currentText()
        config['BASE']['language'] = new_language
        util_writeConfigChanges()
        self.loadLocalizationFile()
        self.applyLocalizationToUi()
        self.updateDialogLocalization()

    def updateAvalibleLanguages(self) -> None:
        self.combox_language.clear()
        av_languages = glob.glob(".\\Localization\\*.yml")
        for lang in av_languages:
            lang = lang.split(".yml")[0].split(".\\Localization\\")[1]
            self.combox_language.addItem(lang)

        # Finding and setting correct index
        found_index = self.combox_language.findText(config['BASE']['language'])
        if found_index != -1:
            self.combox_language.setCurrentIndex(found_index)
        else:
            self.combox_language.setCurrentIndex(0)

    def updateDialogLocalization(self) -> None:
        self.getProcDialog.loc_file = self.loc_file
        self.getProcDialog.setWindowTitle(self.loc_file['PROCESS_DIALOG']['title'])

    # Theme opertaions

    def changeTheme(self) -> None:
        if config['BASE']['theme'] == 0:
            config['BASE']['theme'] = 1
            util_writeConfigChanges()
            self.updateTheme()
            return
        else:
            config['BASE']['theme'] = 0
            util_writeConfigChanges()
            self.updateTheme()
            return

    def updateTheme(self) -> None:
        if config['BASE']['theme'] == 0:
            qdarktheme.setup_theme('dark')
            self.btn_changeTheme.setIcon(self.icon_themeLight)
        else:
            qdarktheme.setup_theme('light')
            self.btn_changeTheme.setIcon(self.icon_themeDark)

    # Hosts operations

    def blockWebsites(self) -> None:
        logging.critical("Trying to block websites by editing 'hosts'")
        try:
            with open(osValues.hostsFile.value, 'r+') as hostsFile:
                hosts_lines = hostsFile.read()
                hostsFile.write('   \n# Blocked websites from SN_Straitjacket\n')
                for site in list(config['BASE']['blocked_websites']):
                    if site not in hosts_lines:
                        if config['PREFERENCES_WEBSITE_REDIR']['is_custom']:
                            hostsFile.write(f"{config['PREFERENCES_WEBSITE_REDIR']['custom_url']} {site}\n")
                        else:
                            hostsFile.write(f"127.0.0.1 {site}\n")
                logging.critical("Sites are blocked!")
        except PermissionError:
            self.info_box.critical(self, self.loc_file['BLOCKING']['webblock_elevation_required_title'],
                                   self.loc_file['BLOCKING']['webblock_elevation_required_content'])
            logging.critical("Permission error!")

    def doHostsBackup(self) -> None:
        logging.critical("Creating a 'hosts' backup file")
        shutil.copy(osValues.hostsFile.value, osValues.hostsFile.value + "_sjbackup")

    def restoreHostsBackup(self) -> None: # Currently does nothing...
        try:
            pass
        except PermissionError:
            pass

    def unblockWebsites(self) -> None: # Restors hosts file with saved backup
        logging.critical("Trying to unblock websites by using 'hosts'")
        try:
            with open(osValues.hostsFile.value, 'r+') as hostsFile:
                hosts_lines = hostsFile.readlines()
                hostsFile.seek(0)
                for line in hosts_lines:
                    if not any(site in line for site in list(config['BASE']['blocked_websites'] + ['# Blocked websites from SN_Straitjacket\n'] + ['   \n'])):
                        hostsFile.write(line)
                hostsFile.truncate()
                logging.critical("Sites are unblocked!")
        except PermissionError:
            self.info_box.critical(self, self.loc_file['BLOCKING']['webunblock_elevation_required_title'],
                                   self.loc_file['BLOCKING']['webunblock_elevation_required_content'])
            logging.critical("Permission error!")

    # Time notification operations

    def checkForNotification(self) -> None:
        if self.lable_time.text() == config['PREFERENCES_TIME_NOTIF']['notif_time']:
            self.showNotification()

    def showNotification(self) -> None:
        logging.warning('Showing time notification...')
        if config['PREFERENCES_TIME_NOTIF']['notif_sound']:
            winsound.PlaySound('sound.wav', winsound.SND_ASYNC)

        if config['PREFERENCES_TIME_NOTIF']['open_app'] and self.isMinimized():
            self.showNormal()

        plyer.notification.notify(title= self.loc_file['NOTIFICATION']['title'],
                                message= self.loc_file['NOTIFICATION']['message'].format(config['PREFERENCES_TIME_NOTIF']['notif_time']),
                                app_name= self.loc_file['NOTIFICATION']['app_name'],
                                app_icon= "icon.ico")
        self.isNotificationPlayed = True

    def updateNotificationTime(self) -> None:
        notifTime = self.tedit_notificationTime.time()
        config['PREFERENCES_TIME_NOTIF']['notif_time'] = notifTime.toString('hh:mm:ss')
        util_writeConfigChanges()

        self.updateTimeNotificationText(notifTime)
        self.info_box.information(self, self.loc_file['NOTIFICATION']['notifset_title'], self.loc_file['NOTIFICATION']['notifset_content'])
        logging.warning("Notification time was changed!")

    def updateTimeNotificationText(self, notifTime: QTime) -> None:
        self.labl_curNotification.setText(self.loc_file['NOTIFICATION']['notifset_text'].format(
            notifTime.hour(), self.loc_file['BASE']['hour'],
            notifTime.minute(), self.loc_file['BASE']['minute'],
            notifTime.second(), self.loc_file['BASE']['second']
        ))

    # Closing an app

    def closeEvent(self, event) -> None: # Unblocking websites and apps after exiting from the main app
        logging.critical("Trying to close the app...")
        if self.mainTimer.isActive():
            match config['ADVANCED_STOP_MODE']['stop_type']:
                case 0:
                    event.accept()
                    logging.critical("App closed.")
                case 1:
                    event.ignore()
                    logging.critical("Closure rejected! Stop mode is set to 'Strict'!")
                case 2:
                    if config['ADVANCED_STOP_MODE']['stop_type'] == 2:
                        passGranted = self.askStopPassword(self.loc_file['WIDGETS']['pass_ask_content_exit'])
                    if not passGranted:
                        event.ignore()
                        logging.critical("Closure rejected! Wrong password!")
                    else:
                        self.stopBlockingProcces()
                        self.unblockWebsites()
                        event.accept()
                        logging.critical("App closed.")
                case _:
                    event.accept()
                    logging.critical("App closed.")
        else:
            event.accept()
            logging.critical("App closed.")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MWindow = MainWindow()
    MWindow.updateTheme()
    app.exec()