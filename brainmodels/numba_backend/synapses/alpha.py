# -*- coding: utf-8 -*-
import brainpy as bp
from numba import prange

__all__ = [
    'Alpha'
]


class Alpha(bp.TwoEndConn):
    """
    Alpha synapse.

    .. math::

        \\frac {ds} {dt} &= x

        \\tau^2 \\frac {dx} {dt} = - 2 \\tau x & - s + \\sum_f \\delta(t-t^f)


    For conductance-based (co-base=True):

    .. math::

        I_{syn}(t) = g_{syn} (t) (V(t)-E_{syn})


    For current-based (co-base=False):

    .. math::

        I(t) = \\bar{g} s (t)

    **Synapse Parameters**

    ============= ============== ======== ===================================================================================
    **Parameter** **Init Value** **Unit** **Explanation**
    ------------- -------------- -------- -----------------------------------------------------------------------------------
    tau_decay     2.             ms       The time constant of decay.

    g_max         .2             µmho(µS) Maximum conductance.

    E             0.             mV       The reversal potential for the synaptic current. (only for conductance-based model)

    co_base       False          \        Whether to return Conductance-based model. If False: return current-based model.

    mode          'scalar'       \        Data structure of ST members.
    ============= ============== ======== ===================================================================================  

    **Synapse Variables**

    An object of synapse class record those variables for each synapse:

    ================== ================= =========================================================
    **Variables name** **Initial Value** **Explanation**
    ------------------ ----------------- ---------------------------------------------------------
    g                  0                  Synapse conductance on the post-synaptic neuron.
    s                  0                  Gating variable.
    x                  0                  Gating variable.  
    ================ ================== =========================================================

    References:
        .. [1] Sterratt, David, Bruce Graham, Andrew Gillies, and David Willshaw. 
                "The Synapse." Principles of Computational Modelling in Neuroscience. 
                Cambridge: Cambridge UP, 2011. 172-95. Print.
    """

    target_backend = ['numpy', 'numba', 'numba-parallel', 'numba-cuda']

    @staticmethod
    def derivative(s, x, t, tau):
        dxdt = (-2 * tau * x - s) / (tau ** 2)
        dsdt = x
        return dsdt, dxdt

    def __init__(self, pre, post, conn, delay=0., tau=2.0, **kwargs):
        # parameters
        self.tau = tau
        self.delay = delay

        # connections
        self.conn = conn(pre.size, post.size)
        self.pre_ids, self.post_ids = conn.requires('pre_ids', 'post_ids')
        self.size = len(self.pre_ids)

        # variables
        self.s = bp.ops.zeros(self.size)
        self.x = bp.ops.zeros(self.size)

        self.w = bp.ops.ones(self.size) * .2
        self.I_syn = self.register_constant_delay('I_syn', size=self.size, delay_time=delay)

        self.integral = bp.odeint(f=self.derivative, method='euler')

        super(Alpha, self).__init__(pre=pre, post=post, **kwargs)

    def update(self, _t):
        for i in prange(self.size):
            pre_id = self.pre_ids[i]

            self.s[i], self.x[i] = self.integral(self.s[i], self.x[i], _t, self.tau)
            self.x[i] += self.pre.spike[pre_id]

            self.I_syn.push(i, self.w[i] * self.s[i])

            # output
            post_id = self.post_ids[i]
            self.post.input[post_id] += self.I_syn.pull(i)
