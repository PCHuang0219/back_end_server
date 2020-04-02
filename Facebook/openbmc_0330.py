#!/usr/bin/python3
####################################################################################################

import re
import time
from lib.ui import UI
from lib.script import Script
from lib.cli.facebook.openbmc import OpenBMC

class OpenBMC_0330(Script):
  def __init__(self, dut, job_id="", image_server = 'None'):
    headline = ['Upgrade CPLD for SMB Board']
		purpose = ['To verify if the CPLD of SMB board can be Upgraded by BMC.']

    self.__dut = dut[1]
    self.image_server = image_server
    super().__init__(headline, purpose, script_path=__file__, job_id=job_id)
    # Start logging the script.
    super().beginLog()

  def run(self):
    """
    Function Name: run
    Purpose: Executes the steps defined by this test case.
    """

    # initialize serial, Telnet and SSH UI with SystemMgmt APIs.
    self.__TELNET = super().initUI(self.__dut.telnet_credentials, self.__dut.platform, OpenBMC)
    self.__cycle = 1
    self.__fail_count = 0
    # ==================================================================================================
		UI.log('STEP#01', 'Set an IP for BMC eth0.')
		self.__TELNET.send('sudo ifconfig eth0 ' + self.__fb.eth0_ip + ' netmask ' + self.__fb.eth0_mask + '\r')
		self.__TELNET.expect(self.__dut.ssh_credentials[5])
		
		for i in range(1, self.__cycle + 1):
			# ==================================================================================================
			UI.log('STEP#02 - cycle#' + str(i) + '/' + str(self.__cycle), 'Use scp funtion to copy SMB update image to BMC then check the image is transfer correctlly.')
			new_smb_cpld_ver = self.__TELNET.getImageVersion(self.__fb_image.local_new_image_path + '/SMBCPLD/version.txt')
			new_smb_cpld_filename = self.__TELNET.getImageFilename(self.__fb_image.local_new_image_path + '/SMBCPLD/version.txt')
			
			UI.log('SMBCPLD (' + new_smb_cpld_filename + ') New version is "' + new_smb_cpld_ver + '".')
			
			server_file_path = self.__fb_image.local_new_image_path.replace(self.__fb_image.local_root_path, '') + '/SMBCPLD/' + new_smb_cpld_filename
			
			self.__TELNET.downloadFile(self.__fb.scp_server_username, self.__fb.scp_server_password, self.__fb.scp_server_ip,
				server_file_path, '/var/tmp/minipack_scm_cpld.vme')
				
			# ==================================================================================================
			UI.log('STEP#03 - cycle#' + str(i) + '/' + str(self.__cycle), 'Use the command to update SMB CPLD.')
			self.__TELNET.send('sv stop mTerm\r')
			self.__TELNET.expect(self.__dut.ssh_credentials[5])
			self.__TELNET.send('cpld_ver.sh | grep SMBCPLD\r')
			self.__TELNET.expect(self.__dut.ssh_credentials[5])
			self.__TELNET.send('scmcpld_update.sh /var/tmp/minipack_smb_cpld.vme\r')
			
			while True:
				if self.__TELNET.expect([self.__dut.ssh_credentials[5], '%'], timeout= 180) == 0:
					break
					
			# ==================================================================================================
			UI.log('STEP#04 - cycle#' + str(i) + '/' + str(self.__cycle), 'Reset the Minipack power and verify the version of SMB CPLD in BMC.')
			self.__TELNET.send('wedge_power.sh reset -s\r')
			
			while True:
				if self.__TELNET.expect(['OpenBMC Release', 'minipack', 'Loading', 'i2c', 'gpio', 'g_cdc'], timeout= 180) == 0:
					break
					
			self.__TELNET.send('\r')
			self.__TELNET.expect('login:')
			self.__TELNET.send(self.__dut.ssh_credentials[3] + '\r')
			self.__TELNET.expect('Password:')
			self.__TELNET.send(self.__dut.ssh_credentials[4] + '\r')
			self.__TELNET.expect(self.__dut.ssh_credentials[5])
			self.__TELNET.send('cpld_ver.sh | grep SMBCPLD\r')
			self.__TELNET.expect(self.__dut.ssh_credentials[5])
			
			result = re.search('(?i)' + new_smb_cpld_ver, self.__TELNET.getBuff(), re.M)
			
			if result == None:
				self.__fail_count += 1
			
				UI.log('FAIL', 'Cycle#' + str(i) + '/' + str(self.__cycle) + ': SMB_CPLD version is NOT match!!')
			else:
				UI.log('PASS', 'Cycle#' + str(i) + '/' + str(self.__cycle) + ': SMB_CPLD version is match!!')
		
		if self.__fail_count == 0:
			UI.log('PASS', 'Cycle#' + str(i) + '/' + str(self.__cycle) + ': BMC_0330 Upgrade_CPLD_for_SMB_Board is passed.')
		else:
			UI.log('FAIL', 'Cycle#' + str(i) + '/' + str(self.__cycle) + ': BMC_0330 Upgrade_CPLD_for_SMB_Board is failed.')

  def stop(self):
    # Terminate interfaces and restore settings.
    self.__TELNET.close()
    # Stop logging the script.
    super().endLog()
