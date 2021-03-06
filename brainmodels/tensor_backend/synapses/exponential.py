# -*- coding: utf-8 -*-
import brainpy as bp

__all__ = [
    'Exponential'
]


class Exponential(bp.TwoEndConn):
    '''
    Single Exponential decay synapse model.

    .. math::
        \\frac{d s}{d t} = -\\frac{s}{\\tau_{decay}}+\\sum_{k} \\delta(t-t_{j}^{k})


    **Synapse Parameters**
    
    ============= ============== ======== ===================================================================================
    **Parameter** **Init Value** **Unit** **Explanation**
    ------------- -------------- -------- -----------------------------------------------------------------------------------
    tau_decay     8.             ms       The time constant of decay.

    ============= ============== ======== ===================================================================================  
    
    **Synapse Variables**

    An object of synapse class record those variables for each synapse:

    ================== ================= =========================================================
    **Variables name** **Initial Value** **Explanation**
    ------------------ ----------------- ---------------------------------------------------------
    s                  0                  Gating variable.

    w                  0                  Synaptic weights.
                             
    ================== ================= =========================================================

    References:
        .. [1] Sterratt, David, Bruce Graham, Andrew Gillies, and David Willshaw. 
                "The Synapse." Principles of Computational Modelling in Neuroscience. 
                Cambridge: Cambridge UP, 2011. 172-95. Print.
    '''

    target_backend = 'general'

    @staticmethod
    def derivative(s, t, tau):
        ds = -s / tau
        return ds

    def __init__(self, pre, post, conn, delay=0., tau=8.0, **kwargs):
        # parameters
        self.tau = tau
        self.delay = delay

        # connections
        self.conn = conn(pre.size, post.size)
        self.conn_mat = conn.requires('conn_mat')
        self.size = bp.ops.shape(self.conn_mat)

        # variables
        self.s = bp.ops.zeros(self.size)
        self.w = bp.ops.ones(self.size) * .1
        self.I_syn = self.register_constant_delay('I_syn', size=self.size, delay_time=delay)

        self.integral = bp.odeint(f=self.derivative, method='exponential_euler')

        super(Exponential, self).__init__(pre=pre, post=post, **kwargs)

    def update(self, _t):
        self.s = self.integral(self.s, _t, self.tau)
        self.s += bp.ops.unsqueeze(self.pre.spike, 1) * self.conn_mat
        self.I_syn.push(self.w * self.s)
        self.post.input += bp.ops.sum(self.I_syn.pull(), axis=0)
