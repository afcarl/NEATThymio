import numpy as np
import parameters as pr
import classes
from Simulation import *
from peas.networks.rnn import NeuralNetwork



class ObstacleAvoidance(Simulation):

	def __init__(self, thymioController, debug, experiment_name):
		super(ObstacleAvoidance, self).__init__(thymioController, debug, experiment_name)
		self.arg = arg
		pass

	def evaluate(self, evaluee):
		fitness = 0
		for i in range(0, pr.eval_time):
			fitness += self.__step(evaluee)
			# print "Fitness at time %d: %d" % (i, fitness)

		# print "Fitness at end: %d" % fitness

		return { 'fitness': fitness }

	def solve(self, evaluee):
		return int(self.evaluate(evaluee)['fitness'] > 1000)

	def __step(self, evaluee):
		# Read sensors: request to ThymioController
		self.__thymioController.readSensorsRequest()
		self.__waitForControllerResponse()
		psValues = self.__thymioController.getPSValues()
		psValues = np.array([psValues[0], psValues[2], psValues[4], psValues[5], psValues[6]])
		# psValues = np.random.standard_normal(5)

		left, right = list(NeuralNetwork(evaluee).feed(psValues)[-2:])

		motorspeed = { 'left': left, 'right': right }

		self.__thymioController.writeMotorspeedRequest((left, right))
		self.__waitForControllerResponse()

		return self.getFitness(motorspeed, psValues)

	def getFitness(self, motorspeed, observation):
		# Calculate penalty for rotating
		speedpenalty = 0
		if motorspeed['left'] > motorspeed['right']:
			speedpenalty = float((motorspeed['left'] - motorspeed['right'])) / float(pr.real_max_speed)
		else:
			speedpenalty = float((motorspeed['right'] - motorspeed['left'])) / float(pr.real_max_speed)
		if speedpenalty > 1:
			speedpenalty = 1

		# Calculate normalized distance to the nearest object
		sensorpenalty = 0
		for i, sensor in enumerate(observation):
			distance = sensor / float(classes.SENSOR_MAX[i])
			if sensorpenalty < distance:
				sensorpenalty = distance
		if sensorpenalty > 1:
			sensorpenalty = 1

		# fitness for 1 timestep in [-1000, 1000]
		return float(motorspeed['left'] + motorspeed['right']) * (1 - speedpenalty) * (1 - sensorpenalty)



CURRENT_FILE_PATH = os.path.abspath(os.path.dirname(__file__))
MAIN_LOG_PATH = os.path.join(CURRENT_FILE_PATH, 'log_main')

def getNextIDPath(path):
	nextID = 0
	filelist = sorted(os.listdir(path))
	if filelist and filelist[-1][0].isdigit():
		nextID = int(filelist[-1][0]) + 1
	return str(nextID)

if __name__ == '__main__':
	from peas.methods.neat import NEATPopulation, NEATGenotype
	genotype = lambda: NEATGenotype(inputs=5, outputs=2)
	pop = NEATPopulation(genotype, popsize=20)

	# Main logger for ThymioController and CommandsListener
	mainLogger = logging.getLogger('mainLogger')
	mainLogger.setLevel(logging.DEBUG)
	mainLogFilename = getNextIDPath(MAIN_LOG_PATH) + '_' + time.strftime("%Y-%m-%d_%H-%M-%S") + '_main_debug.log'
	mainHandler = logging.FileHandler(os.path.join(MAIN_LOG_PATH, mainLogFilename))
	mainHandler.setFormatter(FORMATTER)
	mainLogger.addHandler(mainHandler)
	thymioController = ThymioController(mainLogger)
	
	debug = true
	experiment_name = 'Experiment 001'
	task = ObstacleAvoidance(thymioController, debug, experiment_name)
	
	pop.epoch(generations=100, evaluator=task, solution=task)
