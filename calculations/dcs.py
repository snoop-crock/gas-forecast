from .pvt import PVT


class DKS:
    """Расчет параметров дожимной компрессорной станции"""

    @staticmethod
    def power_calc(Q_mm3day, P_vh, P_vyh, T_K, rho_otn):
        """
        Расчет мощности ДКС (МВт)

        Параметры:
        ----------
        Q_mm3day : float
            Дебит газа (млн.м³/сут)
        P_vh : float
            Давление на входе (МПа)
        P_vyh : float
            Давление на выходе (МПа)
        T_K : float
            Температура газа на входе (K)
        rho_otn : float
            Относительная плотность газа

        Возвращает:
        -----------
        N : float
            Мощность ДКС (МВт)
        """
        if Q_mm3day <= 0:
            return 0.0

        z_vh = PVT.z_factor(P_vh, T_K, rho_otn)
        n = 1.3  # показатель политропы
        k = n / (n - 1)

        N = 2.04 * z_vh * T_K * \
            ((P_vyh / P_vh) ** ((k - 1) / k) - 1) * (Q_mm3day / 0.8)

        return max(0, N)

    @staticmethod
    def Q_max_from_power(N_max, P_vh, P_vyh, T_K, rho_otn):
        """
        Расчет максимального дебита по заданной мощности ДКС (млн.м³/сут)
        """
        if N_max <= 0:
            return 0.0

        z_vh = PVT.z_factor(P_vh, T_K, rho_otn)
        n = 1.3
        k = n / (n - 1)

        Q = N_max / (2.04 * z_vh * T_K *
                     ((P_vyh / P_vh) ** ((k - 1) / k) - 1) * 0.8)

        return max(0, Q)
