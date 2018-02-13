# echos binary inputs

# comments are referencing this:
# https://medium.com/@erikhallstrm/hello-world-rnn-83cd7105b767
# LSTM references http://colah.github.io/posts/2030-08-Understanding-LSTMs/

# TODO name all inputs to functions

from __future__ import print_function, division
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

echo_step = 3  # by how many bits is the input shifted to produce the output
num_epochs = 100  # how many epochs of training should we do?
total_series_length = 50000  # what is total number of bits we should generate?
truncated_backprop_length = 15  # how many bits should be in a single train stream?
state_size = 4  # how many values should be passed to the next hidden layer
num_classes = 2  # defines OUTPUT vector length
batch_size = 5  # how many series to process simultaneously. look at "Schematic of the training data"
# how many batches will be done to go over all the data
batches_per_epoch = total_series_length // batch_size // truncated_backprop_length
learning_rate = 0.5  # rate passed to optimizer (this value is important)

def generateData():
    # 2 defines [0,1] as rand range, then how many, then the odds of each
    x = np.array(np.random.choice(2, total_series_length, p=[0.5, 0.5]))
    y = np.roll(x, echo_step)  # just shifts the whole bit list over by echo_step
    y[0:echo_step] = 0  # sets the beginning values here to be 0 since they are garbage

    # reshape this into a 2d vector where each entry has batch_size elements and an unknown (-1) number of entries in it
    x = x.reshape((batch_size, -1))
    y = y.reshape((batch_size, -1))

    return x, y  # have shapes[batch_size, (remainder)] in this case, [5, 10000]


# input, output, and state types
batchX_placeholder = tf.placeholder(dtype=tf.float32, shape=[batch_size, truncated_backprop_length])
batchY_placeholder = tf.placeholder(dtype=tf.int32, shape=[batch_size, truncated_backprop_length])
init_state = tf.placeholder(dtype=tf.float32,
                            shape=[batch_size, state_size])  # this is a RNN, so we need a state type too

# used to compute the state given the old state and NEW input
# note that this is not an LSTM for at least 1 reason: the OLD output was not fed to us
state_weight = tf.Variable(np.random.rand(state_size + 1, state_size), dtype=tf.float32)
state_bias = tf.Variable(np.zeros(shape=(1, state_size)), dtype=tf.float32)

# used to compute the output given the state
output_weight = tf.Variable(np.random.rand(state_size, num_classes), dtype=tf.float32)
output_bias = tf.Variable(np.zeros(shape=(1, num_classes)), dtype=tf.float32)

# Unpack columns
# keep in mind truncated_backprop_length = 30
# this splits the [truncated_backprop_length, batch_size] tensors into (30) different tensors of shape (5,)
# these are now lists of (30) tensors, each one defining a single cell's input or output per batch
inputs_series = tf.unstack(batchX_placeholder, axis=1)  # axis=1 says to split on the 2nd dimension (indexed on 0)
labels_series = tf.unstack(batchY_placeholder, axis=1)

# Forward pass
current_state = init_state  # current_state will be passed to each next cell
states_series = []  # states_series is (30) elements long because truncated_backprop_length
# defines how the (30) cells that are all joined together pass state. Here we are basically manually unrolling the RNN
# Colors refer to "Schematic of the computations" which you should look at.
# look at tanh in LSTM "The repeating module"
for current_input in inputs_series:
    # defines the input to this cell as having 1 input (green)
    current_input = tf.reshape(tensor=current_input, shape=[batch_size, 1])

    # just combines the input and previous state (green and blue)
    # has shape 5,1 because [batch_size, number of inputs]
    input_and_state = tf.concat(values=[current_input, current_state], axis=1)

    # computes the whole left hand side value of the equation
    lhs = tf.matmul(input_and_state, state_weight) + state_bias  # add b gets applied to each batch automatically

    # use the activation function on each value to compute the next state
    next_state = tf.tanh(lhs)
    states_series.append(next_state)  # remember the state so we can backprop properly
    current_state = next_state  # get the new state

# the input has been wrapped into the states_series list
# LSTM: the states_series is storing the top line having already been tanh, multiplying x and adding bias +
# LSTM: logits_series is the LSTM output ht, computed by tanh(state) * w2 + b
logits_series = [tf.matmul(state, output_weight) + output_bias for state in
                 states_series]  # logits_series is basically output series with size (30)

# apply softmax (which basically just turns our guesses into more appropriate probability guess, (0.1, 0.4)->(0.2, 0.8)
predictions_series = [tf.nn.softmax(logits) for logits in logits_series]

# compute how wrong the guess is by comparing the output(logits) to the correct output (labels)
# https://www.tensorflow.org/api_docs/python/tf/nn/sparse_softmax_cross_entropy_with_logits
losses = [tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=labels) for logits, labels in
          zip(logits_series, labels_series)]

# computes average value across all values in input_tensor (can do more if fed more values)
total_loss = tf.reduce_mean(input_tensor=losses)

# does backprop for us (corrects our tf variables so they are more accurate)
train_step = tf.train.AdagradOptimizer(learning_rate=learning_rate).minimize(total_loss)


def plot(loss_list, predictions_series, batchX, batchY):
    plt.subplot(2, 3, 1)
    plt.cla()
    plt.plot(loss_list)

    for batch_series_idx in range(5):
        one_hot_output_series = np.array(predictions_series)[:, batch_series_idx, :]
        single_output_series = np.array([(1 if out[0] < 0.5 else 0) for out in one_hot_output_series])

        plt.subplot(2, 3, batch_series_idx + 2)
        plt.cla()
        plt.axis([0, truncated_backprop_length, 0, 2])
        left_offset = range(truncated_backprop_length)
        plt.bar(x=left_offset, height=batchX[batch_series_idx, :] * 0.3, bottom=0.6, width=1, color="blue")  # input
        plt.bar(x=left_offset, height=batchY[batch_series_idx, :] * 0.3, bottom=0.3, width=1, color="red")  # output
        plt.bar(x=left_offset, height=single_output_series * 0.3, bottom=0, width=1, color="green")  # network guess

    plt.draw()
    plt.pause(0.0001)


np.set_printoptions(precision=1)
with tf.Session() as sess:
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    plt.ion()
    plt.figure()
    plt.show()
    loss_list = []

    # one epoch will go through all the training data
    # each epoch will call to generate more data
    # (likely to be different data in this case since rand, but generally doesn't have to be if you have limited data)
    for epoch in range(num_epochs):
        x, y = generateData()
        _current_state = np.zeros((batch_size, state_size))

        print("New data, epoch:", epoch)

        for batch_i in range(batches_per_epoch):
            # find where in the data to start for this batch
            start_batch_pos = batch_i * truncated_backprop_length
            end_batch_pos = start_batch_pos + truncated_backprop_length

            # for all lists in this list, grab this range [start_batch_pos:end_batch_pos)
            batchX = x[:, start_batch_pos:end_batch_pos]  # size [5, 30] because [batch_size, truncated_backprop_length]
            batchY = y[:, start_batch_pos:end_batch_pos]  # size [5, 30] because [batch_size, truncated_backprop_length]

            # _total_loss is just the average loss across this batch, so a float
            # _train_step is None
            # _current_state is shape [5, 4] because [batch_size, state_size] it will be fed to next batch
            # _predictions_series has shape [30, 5, 2] because [truncated_backprop_length, batch_size, num_classes]
            _total_loss, _train_step, _current_state, _predictions_series = sess.run(
                [total_loss, train_step, current_state, predictions_series],
                feed_dict={
                    batchX_placeholder: batchX,  # input for this batch
                    batchY_placeholder: batchY,  # output (answers) for this batch
                    init_state: _current_state   # initial state of this batch (hopefully carried over from last time)
                })

            # keep track of the loss values so we can plot them
            loss_list.append(_total_loss)

            # don't display more than n in the graph
            if(len(loss_list) > 2000):
                del loss_list[0]

            # every n batches, print an update
            if batch_i % 100 == 0:
                print("Step:", batch_i, "Loss:", _total_loss)
                # update the plots
                plot(loss_list, _predictions_series, batchX, batchY)

                if batch_i % 500 == 0:
                    mini_batch_prediction = []
                    rounded_prediction = []
                    for batch_series_i in range(1):  # just grab the first one (returns value 0)

                        # predictions_series has shape [30, 5, 2]
                        # because [truncated_backprop_length, batch_size, num_classes]
                        # np.array so we can use fancy index -> [magic, python, indexing]
                        # grab all time outputs, for batch (batch_series_i) and all class output values
                        mini_batch_prediction = np.array(_predictions_series)[:, batch_series_i, :]

                        # each output is a list [num_classes]
                        # decode mini_batch_prediction outputs to go to either 0 or 1 instead of the one hot classes
                        # out[0] can be compared to 0.5 because tf.nn.softmax(logits) turned the guesses
                        # into probabilities.
                        # out[0] is the probability of 0 being the right answer
                        # out[1] is the probability of 1 being the right answer
                        rounded_prediction = np.array([(1 if out[0] < 0.5 else 0) for out in mini_batch_prediction])

                    print("Answer:")
                    print(batchY[0, :])  # batch 0 and all time step outputs
                    print("Prediction:")
                    print(rounded_prediction)
                    print("Resulting State:")
                    print(_current_state[0])  # the resulting state after

plt.ioff()
plt.show()
