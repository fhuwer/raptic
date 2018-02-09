#!/usr/bin/env python3
from dialog import Dialog
from subprocess import check_output, call, CalledProcessError, Popen, DEVNULL
from configparser import ConfigParser
from os.path import abspath, expanduser, expandvars, isfile
from time import sleep


class RAPTIC:
   configuration_options = [
            ('Server', 'Hostname or IP-Address of the ThinClient-Host-Server', str, '', True),
            ('User', 'Username of the user that should be used by this ThinClient', str, '', True),
            ('Fullscreen', 'Run rdesktop in fullscreen mode (default: yes)', bool, 'yes', False),
         ]

   def __init__(self):
      ''' Initialize RAPTIC. '''
      self.dialog = Dialog(dialog='dialog', autowidgetsize=True)
      self.dialog.set_background_title("RAPTIC - an easy thin client for raspberry pi")

      self.__read_config()

   def __read_config(self):
      '''
      Load the configuration for RAPTIC.

      There are multiple locations for the config file. They are used exclusively and are tested in
      the following order:
         - ~/.raptic
         - ~/.config/raptic
      '''
      self.config = ConfigParser()
      for filename in ['~/.raptic', '~/.config/raptic']:
         filename = abspath(expanduser(expandvars(filename)))
         if isfile(filename):
            self.config.read(filename)
            self.__config_path = filename
            return

   def __first_start(self):
      ''' Show dialogs to configure RAPTIC on the first execution. '''
      self.dialog.msgbox(('Welcome to RAPTIC!\nThis appears to be the first time you run RAPTIC on '
         'this PC. We therefore will generate a new configuration in the following steps.'))

      self.config['general'] = {}
      for name, description, option_type, default, required in RAPTIC.configuration_options:
         if required:
            code, value = self.dialog.inputbox(name)
            if code != self.dialog.OK:
               self.dialog.msgbox('Configuration aborted. No configuration file written...')
               self.exit(1)
         else:
            value = default
         self.config['general'][name] = value
      try:
         self.__config_save()
         self.dialog.msgbox('Configuration file has been written. You can now start using RAPTIC.')
      except FileNotFoundError:
         self.dialog.msgbox('Configuration file "{}" is not writeable.'.format(self.__config_path))
         self.exit(1)

   def __config_edit(self):
      ''' Show menu for editing the configuration. '''
      changed_config = ConfigParser()
      changed_config.update(self.config)
      while True:
         code, tag = self.dialog.menu('What setting do you want to change?',
               choices=[(name, changed_config['general'][name]) for name, *_ in
                  RAPTIC.configuration_options], ok_label='CHANGE', cancel_label='BACK',
               extra_button=True, extra_label='SAVE')

         if code == self.dialog.CANCEL:
            return

         if code == self.dialog.OK:
            code_change, value = self.dialog.inputbox(tag, init=changed_config['general'][tag])
            if code_change == self.dialog.OK:
               changed_config['general'][tag] = value

         if code == self.dialog.EXTRA:
            self.config.update(changed_config)
            try:
               self.__config_save()
               self.dialog.infobox('The config has been written to file.', title='RAPTIC')
               sleep(1)
            except FileNotFoundError:
               self.dialog.msgbox('Configuration file "{}" is not writeable.'.format(
                  self.__config_path))
            return

   def __config_save(self):
      ''' Save the configuration to file. '''
      with open(self.__config_path, 'w') as f:
         self.config.write(f)

   def __rdesktop_start(self):
      ''' Run `rdesktop` via `xinit`. '''
      tty = 1
      try:
         rdesktop_path = check_output(['which', 'rdesktop']).decode('utf8').strip()
      except CalledProcessError:
         self.dialog.msgbox(('It appears that rdesktop is not in your PATH. This could be because'
            'of wrong settings or rdesktop is currently not installed.'))
         self.exit(1)

      command = 'xinit {rdesktop} -u {user} {server} {fullscreen} -- {tty}'.format(
            rdesktop=rdesktop_path,
            user = self.config.get('general', 'user'),
            server = self.config.get('general', 'server'),
            fullscreen = '-f' if self.config.getboolean('general', 'fullscreen') else '',
            tty = ':{}'.format(tty) if tty else ''
         )
      call(command, shell=True, stderr=DEVNULL, stdout=DEVNULL)

   def __desktop_environment_start(self):
      ''' Run desktop environment by calling `startx`. '''
      call('startx', shell=True)

   def __menu(self):
      ''' Show the main menu and call the selected action. '''
      code, tag = self.dialog.menu('What do you want to do?',
            choices=[
               ('1', 'Start ThinClient'),
               ('2', 'Change configuration'),
               ('3', 'Start desktop environment'),
               ('x', 'Exit RAPTIC')], nocancel=True)

      if code != self.dialog.OK:
         self.exit(1)

      if tag == '1':
         self.__rdesktop_start()
      elif tag == '2':
         self.__config_edit()
      elif tag == '3':
         self.__desktop_environment_start()
      elif tag == 'x':
         return False
      return True

   def run(self):
      ''' Start RAPTIC. '''
      if not self.config.sections():
         self.__first_start()

      while True:
         if not self.__menu():
            self.exit(0)

   def exit(self, code):
      ''' Clear the screen and exit the application with given status code. '''
      Popen('clear', shell=False, stdout=None, stderr=None, close_fds=True)
      exit(code)
