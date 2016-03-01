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
		global w, h, wTar, hTar
		global v0
		w,h = self.screen.size
		v0 = w/(2*float(self.params['FeedbackDuration'][0])*1000)			# Used to determine the velocity of the cursor

		# Target Dimension
		wTar = 60
		hTar = 240

		# Targets - filled rectangle patch
		self.stimulus('Target', self.VisualStimuli.Block,
						anchor= 'center',
						position= (0, h/2),
						size= [wTar, hTar],
						color= [0, 0.5, 0.5],
					  	on=True)

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
					  position=(w/2, h/2),
					  radius= 20,
					  color= [1, 0.5, 0.5],
					  anchor='center',
					  on= False)
		global cursorSpeed
		cursorSpeed = 30

		# Set initial Targetcode
		self.states['TargetCode'] = 2


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

		self.phase(name='PreFeedback',	next= 'Feedback',		duration= PreFeedbackDuration, 	)
		self.phase(name='Feedback',		next= 'PostFeedback',	duration= MaxFeedbackDuration,	) # MaxFeedbackDuration as hard time limit
		self.phase(name='PostFeedback', next= 'PreFeedback',	duration= PostFeedbackDuration	)

		self.design(start='PreFeedback') # First phase
		
	#############################################################
	
	def Transition(self, phase):
		# present stimuli and update state variables to record what is going on
		if phase == 'PreFeedback':
			# Display current stage
			self.stimuli['SomeText'].text = 'PreFeedback stage'

			# Set state
			if self.states['TargetCode'] == 2:
				self.stimuli['Target'].position = (0, h/2)
				self.states['TargetCode'] = 3  # For nex trial
			elif self.states['TargetCode'] == 3:
				self.stimuli['Target'].position = (w - wTar/2, h/2)
				self.states['TargetCode'] = 2  # For nex trial

			# Return to the initial state
			self.stimuli['Cursor'].position = (w/2, h/2)
			self.stimuli['Cursor'].color = [1, 0.5, 0.5]
			self.stimuli['Target'].color = [0, 0.5, 0.5]

			# HIde cursor
			self.stimuli['Cursor'].on = False


		if phase == 'Feedback':
			# Display current stage
			self.stimuli['SomeText'].text = 'Feedback stage'

			# Set Feedback state to 1 --> Feedback begins
			self.states['Feedback'] = 1

			# Show Cursor
			self.stimuli['Cursor'].on = True


		if phase == 'PostFeedback':
			# Display current stage
			self.stimuli['SomeText'].text = 'PostFeedback stage'

			# Set Feedback state to 0 --> stop Feedback
			self.states['Feedback'] = 0

		
	#############################################################
	
	def Process(self, sig):
		mCursor = self.stimuli['Cursor']
		posX = mCursor.position[0]
		posY = mCursor.position[1]
		if abs(sig.A[0]) <= 1:
			mCursor.position = (float(sig.A[0])*v0*w*10 + w/2, posY)
		else:
			mCursor.position = (posX, posY)

		# print mCursor.position

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

		if self.isTargetHit():
			self.TargetHit()

		
	#############################################################
	
	def StopRun(self):
		pass


	############################################################
	# Self-developed methods
	###########################################################
	def isTargetHit(self): 	# Text collision of 2 objects
		"""Check if any target was hit
		:return: True if hit, False otherwise
		"""
		mCursor = self.stimuli['Cursor']
		mTarget = self.stimuli['Target']
		d = abs(mCursor.position[0] - mTarget.position[0]) 	# distance btw Target and Cursor
		if d < (mCursor.radius + mTarget.size[0]/2):
			return True
		else:
			return False

	def TargetHit(self):
		"""Activities after a Target got hit, including:
		- Change states
		- Light up both Cursor and Target
		- Immediately jump to next phase
		:return:
		"""
		# Change states
		self.states['ResultCode'] = self.states['TargetCode']
		self.states['Feedback'] = 0  	# Stop feedback
		print 'Hit! Target #"%f"' % self.states['ResultCode']

		# Light up Cursor and Target
		hitColor = [1, 1, 1]
		self.stimuli['Cursor'].color = hitColor
		self.stimuli['Target'].color = hitColor

		# Immediately jump to the next phase
		self.change_phase('PostFeedback')

	def moveLeft(self):
		#global cursorSpeed, posX, posY, mCursor
		mCursor = self.stimuli['Cursor']
		posX = mCursor.position[0]
		posY = mCursor.position[1]
		mCursor.position = (posX - cursorSpeed, posY)

	def moveRight(self):
		#global cursorSpeed, posX, posY, mCursor
		mCursor = self.stimuli['Cursor']
		posX = mCursor.position[0]
		posY = mCursor.position[1]
		mCursor.position = (posX + cursorSpeed, posY)



#################################################################
#################################################################
