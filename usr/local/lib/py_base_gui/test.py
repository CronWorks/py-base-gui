from py_base.JobOutput import JobOutput
from py_base_gui.PySystemGui import InputDialog, PySystemGui
from py_base.PySystemMock import PySystemMock

out = JobOutput()
out.setJobOutputVerbosity(out.LOG_LEVEL_MUNDANE)

print '\nTEST 1: runCommandWithPleaseWaitSpinner()'
print 'should show spinner while printing in real time'
system = PySystemMockGui(out, 'PySystemMockGui Test Run')
result = system.runCommandWithPleaseWaitSpinner('PySystemMockGui TEST COMMAND')
print 'function returned result: %s' % result

print '\nTEST 2: runCommandWithPleaseWaitSpinner()'
print 'should show spinner while sleeping 5'
system = PySystemGui(out, 'PySystemGui Test Run')
system.runCommandWithPleaseWaitSpinner(['sleep', '5'])

print '\nTEST 3: Input window'
system = PySystemGui(out, 'PySystemGui Test Run')
inputWindow = InputDialog('Test Input Window',
                          out,
                          system,
                          "A question to ask the user:",
                          'default value',
                          '/home/luke/Reference/Code/Windows/Netsync/Netsync/logo-luke.png',
                          '''
                          the free text\nand more free text
                          this is where the netsync contents will be....
                          like    <----    this.
                          
                          and another go...
                          
                          the free text
                          and more free text
                          this is where the netsync contents will be....
                              like    <----    this.
                          and another go...
                          the free text\nand more free text
                          this is where the netsync contents will be....
                          like    <----    this.
                          
                          and another go...
                          
                          the free text
                          and more free text
                          this is where the netsync contents will be....
                              like    <----    this.
                          and another go...
                          the free text\nand more free text
                          this is where the netsync contents will be....
                          like    <----    this.
                          
                          and another go...
                          
                          the free text
                          and more free text
                          this is where the netsync contents will be....
                              like    <----    this.
                          and another go...
                          the free text\nand more free text
                          this is where the netsync contents will be....
                          like    <----    this.
                          
                          and another go...
                          
                          the free text
                          and more free text
                          this is where the netsync contents will be....
                              like    <----    this.
                          and another go...
                          ''')
print 'showing InputWindow()'
result = inputWindow.show()
print 'InputWindow got result: "%s"' % result

print '\nTEST 4: Input window with a list of default values'
system = PySystemGui(out, 'PySystemGui Test Run')
inputWindow = InputDialog('Test Input Window',
                          out,
                          system,
                          "A question to ask the user:",
                          ['default value 1', 'default value 2', 'default value 3', 'default value 4'],
                          '/home/luke/Reference/Code/Windows/Netsync/Netsync/logo-luke.png',
                          '''
                          the free text\nand more free text
                          this is where the netsync contents will be....
                          like    <----    this.
                          ''')
print 'showing InputWindow()'
result = inputWindow.show()
print 'InputWindow got result: "%s"' % result
