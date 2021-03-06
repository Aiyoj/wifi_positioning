# -*- coding: utf-8 -*-

# @Env      : windows python3.5
# @Author   : xushiqi
# @Email    : xushiqitc@163.com
# @File     : dsae.py
# @Software : PyCharm


import tensorflow as tf
from lib.networks.network import Network
from experiment.hyperparams import HyperParams as hp


class DenosingStackAutoEncoder(Network):
    def __init__(self, data, label):
        self.data = data
        self.label = label
        self.is_training = tf.placeholder(tf.bool)
        self.keep_prob = tf.placeholder(tf.float32)

        self.n_class = label.shape[-1]
        self.n_feature = data.shape[-1]

        self.mask = tf.placeholder(tf.float32, [None, self.n_feature])

        super(DenosingStackAutoEncoder, self).__init__(
            inputs={
                'data': self.data,
                'label': self.label,
                'keep_prob': self.keep_prob,
            },
            trainable=hp.trainable,
            reuse=hp.reuse
        )

    def load(self, data_path, sess, saver):
        pass

    def setup(self):
        # stack auto encoder
        data_denosing = tf.multiply(self.data, self.mask)
        print(data_denosing)
        enc1 = self.fc(data_denosing, hp.hidden_units512, name='enc1', biased=True, activation=hp.activation)
        enc2 = self.fc(enc1, hp.hidden_units256, name='enc2', biased=True, activation=hp.activation)
        encoded = self.fc(enc2, hp.hidden_units128, name='encoded', biased=True, activation=hp.activation)
        dec2 = self.fc(encoded, hp.hidden_units256, name='dec2', biased=True, activation=hp.activation)
        dec1 = self.fc(dec2, hp.hidden_units512, name='dec1', biased=True, activation=hp.activation)
        decoded = self.fc(dec1, self.n_feature, name='decoded', biased=True, activation=False)

        # cls
        fc1 = self.fc(encoded, hp.hidden_units256, name='fc1', biased=True, activation='elu')
        fc2 = self.fc(fc1, hp.hidden_units256, name='fc2', biased=True, activation='elu')
        cls_score = self.fc(fc2, self.n_class, name='cls_score', biased=True, activation='elu')
        cls_prob = tf.nn.softmax(cls_score, name='cls_score')

        self.layers['cls_score'] = cls_score
        self.layers['cls_prob'] = cls_prob
        self.layers['decoded'] = decoded


if __name__ == '__main__':
    import numpy as np
    from lib.datasets.data_info import DataInfo as di
    from lib.datasets.tdata import TData

    # data info
    mall_name = 'm_2467'
    file_path = 'E:/WiFi_Positioning/data/processed/{}.csv'.format(mall_name)
    gbm_path = hp.gbm_path.format(mall_name)
    n_class = di.num_classes[mall_name]
    n_feature = di.num_features[mall_name]
    class_map = di.classes[mall_name]

    tdata = TData(file_path=file_path, n_feature=n_feature, n_class=n_class, class_map=class_map, kfold=5)
    tx, ty, vx, vy = tdata.get_batch_data()

    net = DenosingStackAutoEncoder(tx, ty)

    with tf.Session() as sess:
        tf.global_variables_initializer().run()
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)
        for i in range(1):
            print(i, sess.run(net.get_output('cls_prob'), feed_dict={net.mask: np.ones((hp.batch_size, n_feature))}))
        coord.request_stop()
        coord.join(threads)
