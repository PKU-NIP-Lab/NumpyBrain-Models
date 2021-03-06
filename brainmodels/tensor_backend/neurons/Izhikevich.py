# -*- coding: utf-8 -*-

import brainpy as bp

__all__ = [
    'Izhikevich'
]


class Izhikevich(bp.NeuGroup):
    '''
    The Izhikevich neuron model.

    .. math ::

        \\frac{d V}{d t} &= 0.04 V^{2}+5 V+140-u+I

        \\frac{d u}{d t} &=a(b V-u)

    .. math ::

        \\text{if}  v \\geq 30  \\text{mV}, \\text{then}
        \\begin{cases} v \\leftarrow c \\\\ u \\leftarrow u+d \\end{cases}

    **Neuron Parameters**

    ============= ============== ======== ================================================================================
    **Parameter** **Init Value** **Unit** **Explanation**
    ------------- -------------- -------- --------------------------------------------------------------------------------
    type          None           \        The neuron spiking type.

    a             0.02           \        It determines the time scale of the recovery variable :math:`u`.

    b             0.2            \        It describes the sensitivity of the recovery variable :math:`u` to

                                          the sub-threshold fluctuations of the membrane potential :math:`v`.

    c             -65.           \        It describes the after-spike reset value of the membrane

                                          potential :math:`v` caused by the fast high-threshold :math:`K^{+}` conductance.

    d             8.             \        It describes after-spike reset of the recovery variable :math:`u`

                                          caused by slow high-threshold :math:`Na^{+}` and :math:`K^{+}` conductance.

    t_refractory  0.             ms       Refractory period length. [ms]

    V_th          30.            mV       The membrane potential threshold.
    ============= ============== ======== ================================================================================

    **Neuron Variables**

    An object of neuron class record those variables for each neuron:

    ================== ================= =========================================================
    **Variables name** **Initial Value** **Explanation**
    ------------------ ----------------- ---------------------------------------------------------
    V                          -65        Membrane potential.

    u                          1          Recovery variable.

    input                      0          External and synaptic input current.

    spike                      0          Flag to mark whether the neuron is spiking.

                                          Can be seen as bool.

    t_last_spike               -1e7       Last spike time stamp.
    ================== ================= =========================================================

    References:
        .. [1] Izhikevich, Eugene M. "Simple model of spiking neurons." IEEE
               Transactions on neural networks 14.6 (2003): 1569-1572.

        .. [2] Izhikevich, Eugene M. "Which model to use for cortical spiking neurons?."
               IEEE transactions on neural networks 15.5 (2004): 1063-1070.
    '''
    target_backend = 'general'

    @staticmethod
    def derivative(V, u, t, I_ext, a, b):
        dVdt = 0.04 * V * V + 5 * V + 140 - u + I_ext
        dudt = a * (b * V - u)
        return dVdt, dudt

    def __init__(self, size, a=0.02, b=0.20, c=-65., d=8.,
                 t_refractory=0., V_th=30., **kwargs):
        # params
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.t_refractory = t_refractory
        self.V_th = V_th

        # vars
        num = bp.size2len(size)
        self.V = bp.ops.ones(num) * -65.
        self.u = bp.ops.ones(num) * 1.
        self.input = bp.ops.zeros(num)
        self.spike = bp.ops.zeros(num, dtype=bool)
        self.refractory = bp.ops.zeros(num, dtype=bool)
        self.t_last_spike = bp.ops.ones(num) * -1e7

        self.integral = bp.odeint(self.derivative)
        super(Izhikevich, self).__init__(size=size, **kwargs)

    def update(self, _t):
        V, u = self.integral(self.V, self.u, _t, self.input, self.a, self.b)
        refractory = (_t - self.t_last_spike) <= self.t_refractory
        V = bp.ops.where(refractory, self.V, V)
        u = bp.ops.where(refractory, self.u, u)
        spike = self.V_th <= V
        self.t_last_spike = bp.ops.where(spike, _t, self.t_last_spike)
        self.V = bp.ops.where(spike, self.c, V)
        self.u = bp.ops.where(spike, u + self.d, u)
        self.refractory = refractory | spike
        self.input[:] = 0.
        self.spike = spike
