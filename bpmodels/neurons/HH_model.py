import brainpy as bp
import brainpy.numpy as np

# constant values
E_NA = 50.
E_K = -77.
E_LEAK = -54.387
C = 1.0
G_NA = 120.
G_K = 36.
G_LEAK = 0.03
V_THRESHOLD = 20.

NOISE = 1.

def get_HH (noise=NOISE, V_threshold = V_THRESHOLD, C = C, E_Na = E_NA, E_K = E_K,
             E_leak = E_LEAK, g_Na = G_NA, g_K = G_K, g_leak = G_LEAK):
    '''
    A Hodgkin–Huxley neuron implemented in BrainPy.
    
    Args:
        noise (float): the noise fluctuation. default = 0.
        V_threshold (float): the spike threshold. default = 20. (mV)
        C (float): capacitance. default = 1.0 (ufarad)
        E_Na (float): reversal potential of sodium. default = 50. (mV)
        E_K (float): reversal potential of potassium. default = -77. (mV)
        E_leak (float): reversal potential of unspecific. default = -54.387 (mV)
        g_Na (float): conductance of sodium channel. default = 120. (msiemens)
        g_K (float): conductance of potassium channel. default = 36. (msiemens)
        g_leak (float): conductance of unspecific channels. default = 0.03 (msiemens)
        
    Returns:
        HH_neuron (NeuType).
        
    '''
    
    # define variables and initial values
    ST = bp.types.NeuState(
        {'V': -65., 'm': 0.05, 'h': 0.60, 'n': 0.32, 'spike': 0., 'input': 0.},
        help='Hodgkin–Huxley neuron state.\n'
             '"V" denotes membrane potential.\n'
             '"n" denotes potassium channel activation probability.\n'
             '"m" denotes sodium channel activation probability.\n'
             '"h" denotes sodium channel inactivation probability.\n'
             '"spike" denotes spiking state.\n'
             '"input" denotes synaptic input.\n'
    )
    
    
    # call bp.integrate to solve the differential equations
    
    @bp.integrate
    def int_m(m, t, V):
        alpha = 0.1 * (V + 40) / (1 - np.exp(-(V + 40) / 10))
        beta = 4.0 * np.exp(-(V + 65) / 18)
        return alpha * (1 - m) - beta * m
    
    @bp.integrate
    def int_h(h, t, V):
        alpha = 0.07 * np.exp(-(V + 65) / 20.)
        beta = 1 / (1 + np.exp(-(V + 35) / 10))
        return alpha * (1 - h) - beta * h
    
    @bp.integrate
    def int_n(n, t, V):
        alpha = 0.01 * (V + 55) / (1 - np.exp(-(V + 55) / 10))
        beta = 0.125 * np.exp(-(V + 65) / 80)
        return alpha * (1 - n) - beta * n
    
    @bp.integrate
    def int_V(V, t, m, h, n, input_current):
        I_Na = (g_Na * np.power(m, 3.0) * h) * (V - E_Na)
        I_K = (g_K * np.power(n, 4.0))* (V - E_K)
        I_leak = g_leak * (V - E_K)
        int_V = (- I_Na - I_K - I_leak + input_current)/C 
        return int_V, noise / C
    
    # update the variables change over time (for each step)
    def update(ST, _t_):
        m = np.clip(int_m(ST['m'], _t_, ST['V']), 0., 1.) # use np.clip to limit the int_m to between 0 and 1.
        h = np.clip(int_h(ST['h'], _t_, ST['V']), 0., 1.)
        n = np.clip(int_n(ST['n'], _t_, ST['V']), 0., 1.)
        V = int_V(ST['V'], _t_, m, h, n, ST['input'])  # solve V from int_V equation.
        spike = np.logical_and(ST['V'] < V_threshold, V >= V_threshold) # spike when reach threshold.
        ST['spike'] = spike
        ST['V'] = V
        ST['m'] = m
        ST['h'] = h
        ST['n'] = n
        ST['input'] = 0.   
    
    return bp.NeuType(name='HH_neuron', requires={"ST": ST}, steps=update, vector_based=True)