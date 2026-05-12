from .pvt import PVT


class DKS:
    """Расчет параметров дожимной компрессорной станции"""

    @staticmethod
    def power_calc(Q_mm3day, P_vh, P_vyh, T_K, rho_otn):
        """
        Расчет мощности ДКС (МВт)
        
        Использует формулу для политропного сжатия газа:
        N = 2.04 * Z * T * [pi - 1/pi] * (Q / 800)
        
        где pi = P_выход / P_вход (pressure ratio)
        """
        if Q_mm3day <= 0 or P_vh <= 0:
            return 0.0

        z_vh = PVT.z_factor(P_vh, T_K, rho_otn)
        
        pressure_ratio = P_vyh / P_vh
        
        if pressure_ratio <= 1:
            return 0.0
        
        N = 2.04 * z_vh * T_K * (pressure_ratio - 1.0 / pressure_ratio) * (Q_mm3day / 800.0)
        
        return max(0, N)

    @staticmethod
    def Q_max_from_power(N_max, P_vh, P_vyh, T_K, rho_otn):
        """
        Расчет максимального дебита по заданной мощности ДКС (млн.м³/сут)
        """
        if N_max <= 0 or P_vh <= 0:
            return 0.0

        z_vh = PVT.z_factor(P_vh, T_K, rho_otn)
        
        pressure_ratio = P_vyh / P_vh
        if pressure_ratio <= 1:
            return 0.0
        
        Q = N_max / (2.04 * z_vh * T_K * (pressure_ratio - 1.0 / pressure_ratio)) * 800.0

        return max(0, Q)