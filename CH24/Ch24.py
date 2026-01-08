#load required packages
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.plot import show
from rasterio.fill import fillnodata

#set plot parameters
plt.rcParams['figure.figsize'] = [5, 5]

#open the ponui DTM raster and plot
raw = rasterio.open("D:/GIS/Geomorphometry/data/ponui_island_dtm.tif")
show(raw, 1, cmap='terrain')

#check the dimensions of the raster
print(raw.height, raw.width)

#create empty list to store local raster patches for training
raw_list_a = list()

w = 13 #window size

# extract patches for training

#process one row at a time
for i in range(0, int(raw.height) - w, w):
    print(round(i / (int(raw.height) - w) * 100), "%", sep="", end="\r")
    #process the columns for a given row
    for j in range(0, int(raw.width) - w, w):
        #first read the no data mask to check for nan values
        raw_mask = raw.read_masks(
            1,
            window=((i, i + w), (j, j + w))
        )
        #if there are not nans then read the patch and save it to the list
        if (sum(sum(raw_mask == 0)) == 0):
            raw_block_a = raw.read(
                1,
                window=((i, i + w), (j, j + w))
            )
            raw_list_a.append(raw_block_a)

#clean up memory
del (raw_mask, raw_block_a)

#stack the list of blocks in an array
raw_stack_a = np.stack(raw_list_a, axis=-1)
del(raw_list_a)
print(raw_stack_a.shape)

#load keras tensorflow packages for modelling
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from numpy.random import randint
from random import seed
from numpy import expand_dims
from sklearn.preprocessing import normalize

#check for gpu availability
physical_devices = tf.config.list_physical_devices('GPU')
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

#check the shape of the stacked array
print(raw_stack_a.shape)

#plot a random patch from the stack as a sanity check
plt.rcParams['figure.figsize'] = [5, 5]
n=randint(0, raw_stack_a.shape[2])
plt.imshow(raw_stack_a[:,:,n], cmap='terrain')

#reshape the stack to be compatible with keras input shape
raw_blocks_a = np.reshape(raw_stack_a, (w, w, raw_stack_a.shape[2], 1))
del(raw_stack_a)
raw_blocks_a.shape
raw_blocks_a = np.transpose(raw_blocks_a, [2, 0, 1, 3])

#normalize the patches
def norm(x):
    return (x - np.min(x))/(np.max(x) - np.min(x))

l_a = list()
for i in range(raw_blocks_a.shape[0]):
    l_a.append(norm(raw_blocks_a[i,:,:,:]))

#stack normalized patches
raw_blocks_a = np.stack(l_a, axis=0)

#drop any entries from the first axis with nan
raw_blocks_a = raw_blocks_a[~np.isnan(raw_blocks_a).any(axis=(1,2,3))]
del(l_a)

#check the shape and value range of the normalized patches
print(raw_blocks_a.shape)
print(np.min(raw_blocks_a[42,:,:,:]), np.max(raw_blocks_a[42,:,:,:]))

n = randint(0, raw_blocks_a.shape[0])
plt.imshow(raw_blocks_a[n,:,:,:])

#split the data into training and testing sets
train, test = train_test_split(raw_blocks_a, test_size = 0.1, random_state = 42)
print(len(train), len(test))

#set CNN training parameters
k=3 #kernel size
interp='bilinear' #interpolation method for upsampling
opt=keras.optimizers.Adam() #optimizer
epochs=25 #number of training epochs
ft = 6 #number of features in the bottleneck layer

#build the CNN autoencoder model
visible1 = keras.Input(shape=(w,w,1))

e3_a = layers.Conv2D(filters = 64, kernel_size=k, padding = 'same')(visible1)
e3_a = layers.PReLU()(e3_a)
e3_a = layers.MaxPooling2D((2,2))(e3_a)
e3_a = layers.Conv2D(filters = 32, kernel_size=k, padding = 'same')(e3_a)
e3_a = layers.PReLU()(e3_a)
e3_a = layers.MaxPooling2D((2,2))(e3_a)
e3_a = layers.Conv2D(filters = 16, kernel_size=k, padding = 'same')(e3_a)
e3_a = layers.PReLU()(e3_a)
e3_a = layers.MaxPooling2D((3,3))(e3_a)

neck = layers.Conv2D(filters = ft, kernel_size=1)(e3_a)

d3_a = layers.UpSampling2D((3,3), interpolation=interp)(neck)
d3_a = layers.Conv2D(filters=16, kernel_size=k, padding='same')(d3_a)
d3_a = layers.PReLU()(d3_a)
d3_a = layers.UpSampling2D((2,2), interpolation=interp)(d3_a)
d3_a = layers.Conv2D(filters=32, kernel_size=k, padding='same')(d3_a)
d3_a = layers.PReLU()(d3_a)
d3_a = layers.UpSampling2D((2,2), interpolation=interp)(d3_a)
# upsample and add one extra row and column
d3_a = layers.ZeroPadding2D(padding=((1, 0), (1, 0)))(d3_a)
d3_a = layers.Conv2D(filters=64, kernel_size=k, padding='same')(d3_a)
d3_a = layers.PReLU()(d3_a)

out1 = layers.Conv2D(filters=1, kernel_size=1, padding='same', activation='sigmoid', name='output_a')(d3_a)

#assemble and compile the model
model = keras.Model(inputs=[visible1], outputs=[out1])
model.summary()
model.compile(optimizer=opt, loss=['MSE'])

#train the autoencoder end to end
history=model.fit(
    x=train,
    y=train,
    batch_size = 32,
    validation_data = (test, test),
    verbose=1,
    epochs=epochs
)

#plot training and validation loss
plt.plot(history.history['loss'], linewidth = 1, color = 'blue')
plt.plot(history.history['val_loss'], linewidth = 1, color = 'red')

#make predictions on training and testing data
pred = model.predict([train], verbose=1)
pred_test = model.predict(test, verbose=1)
pred.shape

#plot examples of original and reconstructed patches
plt.figure()
plt.rcParams['figure.figsize'] = [10, 5]

r = 1
c = 2

n = randint(0, len(train))
plt.subplot(r, c, 1)
plt.imshow(train[n,:,:,0])
plt.subplot(r, c, 2)
plt.imshow(pred[n,:,:,0])

n = randint(0, len(test))
plt.subplot(r, c, 1)
plt.imshow(test[n,:,:,0])
plt.subplot(r, c, 2)
plt.imshow(pred_test[n,:,:,0])

#extract the encoder model for feature prediction
model_neck = keras.Model(inputs=[visible1], outputs=neck)

#fill a continuous rectangular DTM surface for CNN prediction
data = raw.read(1, masked=True)
mask = raw.read_masks(1)
show(data)
show(mask)
nodata = raw.nodata

#set no data values that will be filled
mask[data == nodata] = 0
data[mask == 0] = -1
data[data < 0] = 0
show(data)

#save data to a temporary file if needed
#np.savez("D:/GIS/Geomorphometry/temp/full_patch.npz", r2=data)

#import packages for prediction
import os
import gc
import glob
import numpy as np
import matplotlib.pyplot as plt

#plot the filled DTM data
r2 = data
plt.imshow(r2)
r2.shape[0]

#copy the raster for working
r3 = np.copy(r2)

#get the dimensions of the raster
height = r3.shape[0]
width = r3.shape[1]

#subset the raster for prediction and writing
n = 50 #subdivide into n sets of rows for prediction
m = int(
    np.floor((r3.shape[0]-w)/n)
)
m #process m rows at a time

#set up a temp directory for storing intermediate files
temp = 'D:/GIS/Geomorphometry/temp/'
for f in glob.glob(temp + '*'):
    os.remove(f)

#process the raster in chunks and save intermediate feature files
for l in range(n):
    print(l, end = '\r')
    raw_list = list()
    #extract patches for training
    for i in range(m*l, m*(l+1), 1):
        for j in range(0, int(int(r3.shape[1]))-w, 1):
            raw_list.append(
                norm(
                    r3[i:i + w, j:j + w]
                )
            )
    #stack and reshape patches for prediction
    raw_stack = np.stack(raw_list, axis=-1)
    auto_blocks = np.reshape(raw_stack, (w, w, raw_stack.shape[2], 1))
    auto_blocks = np.transpose(auto_blocks, [2, 0, 1, 3])
    del(raw_stack)
    #predict features using the encoder model
    pred = model_neck.predict(auto_blocks)
    #clean up and save intermediate files
    del(auto_blocks)
    np.save(file = temp+'p'+str(l)+'.npy', arr = pred)
    del(pred)
    gc.collect()

#process any remaining rows
l = n
print(l, end = '\r')

raw_list = list()

#extract patches for training
for i in range(m*l, int(np.floor(r3.shape[0]-w)), 1):
    for j in range(0, int(int(r3.shape[1]))-w, 1):
        raw_list.append(
            norm(
                r3[i:i + w, j:j + w]
            )
        )
#stack and reshape patches for prediction
raw_stack = np.stack(raw_list, axis=-1)
auto_blocks = np.reshape(raw_stack, (w, w, raw_stack.shape[2], 1))
auto_blocks = np.transpose(auto_blocks, [2, 0, 1, 3])
#predict features using the encoder model
pred = model_neck.predict(auto_blocks)
#clean up and save intermediate files
np.save(file = temp+'p'+str(l)+'.npy', arr = pred)
del(pred)
gc.collect()

#read in all temp files and rasterize
#process one feature at a time
for j in range(ft):
    print(j, end='\r')
    l = list()
    #read in each temp file and extract the jth feature
    for i in range(len(os.listdir(temp))):
        pred = np.load(os.path.join(temp + 'p' + str(i) + '.npy'))
        pred = np.reshape(pred, (pred.shape[0], ft))
        l.append(pred[:, j])
    #concatenate all predicted feature patches into a raster with appropriate dimensions
    l = np.concatenate(l)
    l = np.reshape(l, (r3.shape[0] - w, r3.shape[1] - w))

    #pad the raster to match original dimensions if needed
    row_pad = np.ones(shape=(int(np.floor(w / 2)), l.shape[1]), dtype=l.dtype)
    l = np.append(row_pad, l, axis=0)

    col_pad = np.ones(shape=(l.shape[0], int(np.floor(w / 2))), dtype=l.dtype)
    l = np.append(col_pad, l, axis=1)

    #write the feature raster to file
    aff = rasterio.transform.from_origin(raw.bounds[0], raw.bounds[3], raw.res[0], raw.res[1])
    ref = raw.crs
    dir_name = 'D:/GIS/Geomorphometry/out/ft_6/auto_ft_' + str(j) + '.tif'
    cnn_ft = rasterio.open(
        dir_name,
        'w',
        driver='GTiff',
        height=l.shape[0],
        width=l.shape[1],
        count=1,
        dtype=r3.dtype,
        crs=ref,
        transform=aff
    )
    cnn_ft.write(l, 1)
    cnn_ft.close()