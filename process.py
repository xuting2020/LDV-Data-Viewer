from scipy import signal, fftpack, interpolate
import numpy as np

def band_filter(z ,f1 ,f2 ,fs):
    '''
    BUTTER FILTER
    Z: IN DISPLACEMENT UNIT METER
    F1,F2: BANDPASS FREQ
    FS: SAMPLE RATE
    return filtered,fs
    '''

    sig = z  # z and sig is speed in m/s
    '''BUTTER FILTER '''
    sos = signal.butter(5, [f1, f2], 'bandpass', fs=fs, output='sos')
    filtered = signal.sosfilt(sos, sig  )  # is speed in m/s

    return filtered

def filtfilter(z, freq_lo, freq_hi, fs):
    '''
    filtfilter
    args:
         Z: IN DISPLACEMENT UNIT METER
        freq_lo,freq_hi: BANDPASS FREQ
        fs: SAMPLE RATE
    return: filtered z
    '''
    sos = signal.butter(8, [freq_lo, freq_hi], 'bandpass', fs=fs, output='sos')
    filter_z = signal.sosfiltfilt(sos, z)
    return filter_z

def find_max_dz_ind(z):
    '''
    to find max_dz index(the point which has the largest max(z)-min(z) gap)
    args: z
    return: max_dz index
    '''
    max_dz_ind = np.argmax(np.max(z, axis=1) - np.min(z, axis=1))
    return max_dz_ind

def find_max_dz_data(x_list, y_list, z_list, a_list):
    max_xi_array, max_yi_array, max_zi_array, max_ai_array = [], [], [], []
    for i in range(len(x_list)):
        xi = x_list[i]
        yi = y_list[i]
        zi = z_list[i]
        ai = a_list[i]

        max_dz_ind = find_max_dz_ind(zi)
        print("max_dz_ind", max_dz_ind)

        max_xi_array.append(xi[max_dz_ind])
        max_yi_array.append(yi[max_dz_ind])
        max_zi_array.append(zi[max_dz_ind, :])
        max_ai_array.append(ai[max_dz_ind, :])

    return max_xi_array, max_yi_array, max_zi_array, max_ai_array

def stack_data_list(x_list, y_list, z_list, C_list, a_list):
    '''
    to stack data files
    args: x,y,z,C,a(in list)
    return: x,y,z,C,a(stacked)
    '''
    x = np.hstack(x_list)
    y = np.hstack(y_list)
    z = np.vstack(z_list)
    C = np.hstack(C_list)
    a = np.vstack(a_list)
    return x, y, z, C, a

def calc_env_z(z):
    '''
    to calculate the envolope of z
    args: z
    return: env_z
    '''
    dhil_z = z
    hil_z = fftpack.hilbert(dhil_z)
    env_z = np.sqrt(dhil_z ** 2 + hil_z ** 2)
    return env_z

def phase_amplitude(x, y, z, fs=500e6, s_num=1000):
    '''
    x,y : place ,filtered : displacement in meter after FILTER ,fs: sample rate,s_um: smooth

    Q:  THE INDEX OF BEST SIGNAL
    CN: FFT( FILTERED IN TIME )
    FREQ_OMEGA: OMEGA TO EACH TIME POINT
    M: INDEX  OF MAX SIGNAL IN Q (IN FREQUENCY DOMAIN)
    CM:  MAX SPECTRUM IN ALL VIBRATION_POINTS
    CM_D: NORMALIZE TO MAX DISPLACEMENT
    AMPLITUDE=AMPLITUDE_D: DISPLACEMENT
    ANGLE: Return the angle of the complex argument.
    A_SMOOTH: Smooth bivariate!!! spline approximation
    A_SMOOTH.EV: Evaluate the spline at points

    '''

    num_sig = z[0, :].size  # 6000
    print("num_sig", num_sig)

    field = z
    q = np.argmax(np.max(field, axis=1) - np.min(field, axis=1))
    print('phase_amp', q)

    Cn = np.fft.fft(field, axis=1)  # belongs to complex
    freq_omega = np.fft.fftfreq(num_sig, 1 / fs)  # output is omega

    # find largest frequency component at the space point q
    m = np.argmax(np.abs(Cn[q, :]))
    # find biggest spectrum at line q in number
    # Cm_v=np.max(filtered[q,:])-np.min(filtered[q,:])
    Cm = Cn[:, m]
    Cm_d = Cm / np.max(Cm) * np.max(field[q, :])  # Cm belong to freq domain, field belong to time domain
    # Cm_d =Cm/np.max(Cm)*np.max(field[:,m])#!!!may cause displacement change
    # find spectrum m (frequency) at every line (cell)
    freq = abs(freq_omega[m])

    amplitude = np.abs(Cm_d)  # displacement in meter
    amplitude_d = amplitude
    # amplitude_d = np.abs(Cm_d)/freq*1e9 #displacement in nm
    # amplitude_d=amplitude_d/np.max(amplitude_d)*Cm_v
    angle = np.angle(Cm)  # phase #Return the angle of the complex argument.

    a_smooth = interpolate.SmoothBivariateSpline(x, y, amplitude, s=s_num)
    amp_inter = np.abs(a_smooth.ev(x, y))

    return freq, amplitude, amplitude_d, amp_inter, angle, freq_omega

def phase_amplitude(x, y, filtered, clim=1.):
    '''
    to calculate phase,amplitude,angle
    args: x,y,filtered(z)
    return: phase,amplitude,V(an arg for plot)
    '''
    q = np.argmax(np.max(filtered, axis=1) - np.min(filtered, axis=1))
    Cn = np.fft.fft(filtered, axis=1)  # belongs to complex
    m = np.argmax(np.abs(Cn[q, :]))
    Cm = Cn[:, m]
    # print("Cm.shape",Cm.shape)
    amplitude = np.abs(Cm)
    angle = np.angle(Cm)  # phase
    V = clim *np.linspace(0, np.max(amplitude), 20)

    return angle,amplitude,V


