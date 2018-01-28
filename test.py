import tensorflow as tf

# define the sizes the sizes of input
num_inputs = 1
num_labels = 1

# None says you can feed any number of inputs, every value after declares the shape of those inputs
inputType = tf.placeholder(shape=[None, num_inputs], dtype=tf.float32)
outputType = tf.placeholder(shape=[None, num_labels], dtype=tf.float32)


def build_network(ins):
    layer = tf.layers.dense(name="vars1", inputs=ins, units=num_labels)
    return layer


network = build_network(inputType)
loss = tf.square(outputType - network)
# "vars1/kernel" for weights, "vars1/bias" for biases, and "vars1/kernel:0" for the first weight, etc.
vars1 = tf.get_collection(key=tf.GraphKeys.TRAINABLE_VARIABLES, scope="vars1")
train_op = tf.train.AdamOptimizer(0.1).minimize(loss=loss)  # var_list=[vars1, vars2])

init_op = tf.global_variables_initializer()
sess = tf.Session()
sess.run(init_op)

# Set the expected inputs and outputs.
inputs = [[0], [1], [2]]  # x values
outputs = [[0], [1], [2]]  # expected y values

# Setup the saver and graph writer.
brainSaver = tf.train.Saver(var_list={"vars1": vars1[0]})
graphWriter = tf.summary.FileWriter("output/", sess.graph)

# brainSaver.restore(sess, "brains/test.txt")

# Print initial values of vars1.
print("\n Initial Network [weight, bias]:")
print(sess.run(vars1))

# Train the network for N training events.
for i in range(100):
    print(sess.run(network, feed_dict={inputType: inputs}))  # print the results of each output run.
    sess.run(fetches=[train_op], feed_dict={inputType: inputs, outputType: outputs})  # feed fetches to make it train.

# Print a single sample output.
print("\n Final Outputs For:", inputs)
print(sess.run(network, feed_dict={inputType: inputs}))  # we don't feed fetches, so it jus runs the network.

# see how the network generalizes to new values it hasn't seen before
test_cases = [[5], [75], [2500]]
print("\n Outputs For Test Cases:", test_cases, "(the network has never seen these values before)")
print(sess.run(network, feed_dict={inputType: test_cases}))

# Print values of vars1.
print("\n Final Network [weight, bias]:")
print(sess.run(vars1))

# Save the trained network values and write to the tensor-board.
brainSaver.save(sess, "brains/test.txt")
graphWriter.close()

