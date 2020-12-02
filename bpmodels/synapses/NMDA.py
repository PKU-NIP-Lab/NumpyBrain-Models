# -*- coding: utf-8 -*-

import brainpy as bp
import brainpy.numpy as np


def get_NMDA(g_max=0.15, E=0, alpha=0.062, beta=3.57, 
            cc_Mg=1.2, tau_decay=100., a=0.5, tau_rise=2.):
    """NMDA conductance-based synapse.

    .. math::

        I_{syn} &= \\bar{g}_{syn} s (V-E_{syn})

        g(t) &= \\bar{g} \\cdot g_{\\infty}
        \\cdot \\sum_j s_j(t)

        g_{\\infty}(V,[{Mg}^{2+}]_{o}) &= (1+{e}^{-\\alpha V}
        \\frac{[{Mg}^{2+}]_{o}} {\\beta})^{-1} 

        \\frac{d s_{j}(t)}{dt} &= -\\frac{s_{j}(t)}
        {\\tau_{decay}}+a x_{j}(t)(1-s_{j}(t)) 

        \\frac{d x_{j}(t)}{dt} &= -\\frac{x_{j}(t)}{\\tau_{rise}}+
        \\sum_{k} \\delta(t-t_{j}^{k})

    where the decay time of NMDA currents is taken to be :math:`\\tau_{decay}` =100 ms,
    :math:`a= 0.5 ms^{-1}`, and :math:`\\tau_{rise}` =2 ms (Hestrin et al., 1990 [1]_;
    Spruston et al., 1995[2]_).


    ST refers to the synapse state, items in ST are listed below:
    
    =============== ======== =========================================================
    **Member name** **Type** **Explanation**
    --------------- -------- ---------------------------------------------------------
    s               float    Gating variable.
    
    g               float    Synapse conductance.

    x               float    Gating variable.
    =============== ======== =========================================================


    Args:
        g_max (float) : The maximum conductance.
        E (float) : The reversal potential.
        alpha (float) : Binding constant.
        beta (float) : Unbinding constant.
        cc_Mg (float) : concentration of Magnesium ion.
        tau_decay (float) : The time constant of decay.
        tau_rise (float) : The time constant of rise.
        a (float)
        
    References:
        .. [1] Hestrin, S., et al. "Analysis of excitatory 
               synaptic action in pyramidal cells using whole‐cell 
               recording from rat hippocampal slices." 
               The Journal of Physiology 422.1 (1990): 203-225.
    
        .. [2] Spruston, Nelson, Peter Jonas, and Bert Sakmann. 
               "Dendritic glutamate receptor channels in rat hippocampal 
               CA3 and CA1 pyramidal neurons." The Journal of physiology 482.2 (1995): 325-352.
    
    """
    requires = dict(
        ST=bp.types.SynState(['x', 's', 'g']),
        pre=bp.types.NeuState(['spike']),
        post=bp.types.NeuState(['V', 'input']),
        pre2syn=bp.types.ListConn(),
        post_slice_syn=bp.types.Array(dim=2),
    )

    @bp.integrate
    def int_x(x, _t_):
        return -x / tau_rise

    @bp.integrate
    def int_s(s, _t_, x):
        return -s / tau_decay + a * x * (1 - s)

    def update(ST, _t_, pre, pre2syn):
        for pre_id in range(len(pre2syn)):
            if pre['spike'][pre_id] > 0.:
                syn_ids = pre2syn[pre_id]
                ST['x'][syn_ids] += 1.
        x = int_x(ST['x'], _t_)
        s = int_s(ST['s'], _t_, x)
        ST['x'] = x
        ST['s'] = s
        ST['g'] = g_max * s

    @bp.delayed
    def output(ST, post, post_slice_syn):
        num_post = post_slice_syn.shape[0]
        g = np.zeros(num_post, dtype=np.float_)
        for post_id in range(num_post):
            idx = post_slice_syn[post_id]
            g[post_id] = np.sum(ST['g'][idx[0]: idx[1]])
        I_syn = g * (post['V'] - E)
        g_inf = 1 + cc_Mg / beta * np.exp(-alpha * post['V'])
        post['input'] -= I_syn * g_inf

    return bp.SynType(name='NMDA_synapse',
                      requires=requires,
                      steps=(update, output),
                      vector_based=True)

