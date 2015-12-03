import cPickle as pickle
import numpy as np

distances = np.zeros((240, 320))
point = 120, 320

for x in range(240):
    for y in range(320):
        distances[x, y] = np.sqrt((x - .5 - point[0]) ** 2 +
                                  (y - .5 - point[1]) ** 2)

pickle.dump(distances, open("distances.p", "wb"))
