'''
The program is designed based on the following template:

######################################################################
Sequences of events 	Phases			Typical Application Behaviours
######################################################################

OnPreflight
OnInitialize
OnStartRun								Display initial message
DoPreRun				PreRun
Loop
{
	OnTrialBegin						Display target
	DoFeedback			PreFeedback
	OnFeedbackBegin
	DoFeedback			Feedback		Update cursor position
	OnFeedbackEnd						Hide cursor, mark target as hit
	DoPostFeedback		PostFeedback
	OnTrialEnd							Hide target
	DoITI				ITI
}
OnStopRun
OnHalt

Target Code and the corresponding location
---------------------------
|          ##1##          |
|#                       #|
|2                       3|
|#                       #|
|          ##4##          |
---------------------------

#######################################################################
'''
import numpy
#import PygameRenderer
	
#################################################################
#################################################################
from BCPy2000.GenericApplication import BciGenericApplication


class BciApplication(BciGenericApplication):
	
	#############################################################
	
	def Description(self):
		return "I bet you won't bother to change this to reflect what the application is actually doing"
		
	#############################################################
	
	def Construct(self):
		# supply any BCI2000 definition strings for parameters and
		# states needed by this module
		params = [
			
		]
		states = [
			"SomeState 1 0 0 0",
		]
		
		return params,states
		
	#############################################################
	
	def Preflight(self, sigprops):
		# Here is where you would set VisionEgg.config parameters,
		# either using self.screen.setup(), or directly.
		self.screen.setup(frameless_window=0)  # if using VisionEggRenderer, this sets, VISIONEGG_FRAMELESS_WINDOW
		
	#############################################################
	
	def Initialize(self, indim, outdim):
		# Set up stimuli. Visual stimuli use calls to
		# self.stimulus(). Attach whatever you like as attributes
		# of self, for easy access later on. Don't overwrite existing
		# attributes, however:  using names that start with a capital
		# letter is a good insurance against this.
		
		Text = self.VisualStimuli.Text   # the convention is that the self.VisualStimuli "virtual module"
		                                 # contains at least Text, Disc, Block and ImageStimulus classes for all renderers

		# Screensize
		w,h = self.screen.size

		# Target Dimension
		wTar = 60
		hTar = 240

		# Target - filled rectangle patch
		self.stimulus('Target', self.VisualStimuli.Block,
						anchor= 'upperleft',
						position= [0, h*0.8],
						size= [wTar, hTar],
						color= [0, 0.5, 0.5])

		# Config Screen
		self.screen.SetDefaultFont('comic sans ms', 30)
		self.screen.bgcolor = [0., 0., 0.]

		# Some text on the middle of the screen
		self.stimulus('SomeText', Text, text='This is PyCursorTask',
		                                position=(w/2,h/4),
		                                anchor='top'         )
		self.color = numpy.array([0.0, 0.0, 1.0])

		# Cursor - a filled circle
		self.stimulus('Cursor', self.VisualStimuli.Disc,
					  position=[w/2, h/2],
					  radius= 20,
					  color= [1, 0.5, 0.5])
		cursorSpeed = 30
		mCursor = self.stimuli['Cursor']
		posX = mCursor.position[0]
		posY = mCursor.position[1]



	#############################################################
	
	def StartRun(self):
		pass
		
	#############################################################
	
	def Phases(self):
		# define phase machine using calls to self.phase and self.design
		PreFeedbackDuration = float(self.params['PreFeedbackDuration'][0])*1000 	# return ms
		FeedbackDuration = float(self.params['FeedbackDuration'][0])*1000			# Used to determine the velocity of the cursor
		PostFeedbackDuration = float(self.params['PostFeedbackDuration'][0])*1000
		MaxFeedbackDuration = float(self.params['MaxFeedbackDuration'][0])*1000

		self.phase(name='PreFeedback', 	duration= 		PreFeedbackDuration, 	next= 'Feedback')
		self.phase(name='Feedback',		duration= 		MaxFeedbackDuration,	next= 'PostFeedback') # MaxFeedbackDuration as hard time limit
		self.phase(name='PostFeedback', duration=		PostFeedbackDuration,	next= 'PreFeedback')

		self.design(start='PreFeedback')
		
	#############################################################
	
	def Transition(self, phase):
		global h, wTar, hTar
		# present stimuli and update state variables to record what is going on
		if phase == 'PreFeedback':
			# Display current stage
			self.stimuli['SomeText'].text = 'PreFeedback stage'


			# Set state
			if self.stimuli['LeftTarget'].on:
				self.states['TargetCode'] = 2 	# TargetCode != 0 --> Trial begin
			elif self.stimuli['RightTarget'].on:
				self.states['TargetCode'] = 3

			# Display Target
			self.stimuli['LeftTarget'].on = not self.stimuli['LeftTarget'].on
			self.stimuli['RightTarget'].on = not self.stimuli['RightTarget'].on
			self.stimuli['Cursor'].on = False 	# we dont wanna see the cursor until the Feedback stage

		if phase == 'Feedback':
			# Display current stage
			self.stimuli['SomeText'].text = 'Feedback stage'

			# Set Feedback state to 1 --> Feedback begins
			self.states['Feedback'] = 1

			# Move Cursor
			self.stimuli['Cursor'].on = True

		if phase == 'PostFeedback':
			# Display current stage
			self.stimuli['SomeText'].text = 'PostFeedback stage'

			# Set Feedback state to 0 --> stop Feedback
			self.states['Feedback'] = 0
		
	#############################################################
	
	def Process(self, sig):
		# process the new signal packet
		pass  # or not.
		
	#############################################################
	
	def Frame(self, phase):
		# update stimulus parameters if they need to be animated on a frame-by-frame basis
		intensity = 0.5 + 0.5 * numpy.sin(2.0 * numpy.pi * 0.5 * self.since('run')['msec']/1000.0)
		self.screen.bgcolor = intensity * self.color
		
	#############################################################
	
	def Event(self, phase, event):
		mCursor = self.stimuli['Cursor']

		# respond to pygame keyboard and mouse events
		import pygame.locals
		if event.type == pygame.locals.KEYDOWN:
			if event.key == ord('r'): self.color[:] = [1,0,0]
			if event.key == ord('g'): self.color[:] = [0,1,0]
			if event.key == ord('b'): self.color[:] = [0,0,1]
			if event.key == pygame.K_LEFT: self.moveLeft()
			if event.key == pygame.K_RIGHT: self.moveRight()
		
	#############################################################
	
	def StopRun(self):
		pass


	############################################################
	# Self-developed methods
	###########################################################
	def isTargetHitself(self):
		mCursor = self.stimuli['Cursor']
		return True

	def TargetHit(self):
		hitColor = [0.8, 0.8, 0.8]
		self.stimuli['Cursor'].color = hitColor
		self.stimuli['Target'].color = hitColor

	def moveLeft(self):
		global cursorSpeed, posX, posY, mCursor
		mCursor.position = (posX - cursorSpeed, posY)

	def moveRight(self):
		global cursorSpeed, posX, posY, mCursor
		mCursor.position = (posX + cursorSpeed, posY)

#################################################################
#################################################################
