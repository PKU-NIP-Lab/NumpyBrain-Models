# -*- coding: utf-8 -*-

import brainpy as bp
import matplotlib.pyplot as plt
import brainmodels

bp.backend.set('numba')
duration = 100.
dt = 0.02

size = 10

neu_pre = brainmodels.neurons.LIF(size, monitors=['V', 'input', 'spike'], )
neu_pre.V_rest = -65.
neu_pre.V_reset = -70.
neu_pre.V_th = -50.
neu_pre.V = bp.ops.ones(size) * -65.

neu_post = brainmodels.neurons.LIF(size, monitors=['V', 'input', 'spike'], )

syn_GABAb = brainmodels.synapses.GABAb2(
    pre=neu_pre, post=neu_post, conn=bp.connect.All2All(),
    delay=10., monitors=['s']
)

I, dur = bp.inputs.constant_current([(25, 20), (0, 1000)])
net = bp.Network(neu_pre, syn_GABAb, neu_post)
net.run(dur, inputs=[(neu_pre, 'input', I)], report=True)

# paint gabab
ts = net.ts
fig, gs = bp.visualize.get_figure(2, 1, 5, 6)

fig.add_subplot(gs[0, 0])
plt.plot(ts, syn_GABAb.mon.s[:, 0], label='s')
plt.legend()

fig.add_subplot(gs[1, 0])
plt.plot(ts, neu_post.mon.V[:, 0], label='post.V')
plt.legend()

plt.show()