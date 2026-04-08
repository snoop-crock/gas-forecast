import numpy as np


class PVT:
    """Расчет PVT свойств газа"""

    @staticmethod
    def z_factor(P_MPa, T_K, rho_otn, method='latonov'):
        """
        Расчет коэффициента сверхсжимаемости

        Параметры:
        ----------
        P_MPa : float
            Давление в МПа
        T_K : float
            Температура в Кельвинах
        rho_otn : float
            Относительная плотность газа
        method : str
            Метод расчета ('latonov', 'brown', 'poly')

        Возвращает:
        -----------
        z : float
            Коэффициент сверхсжимаемости
        """
        # Критические параметры
        T_cr = 92.2 + 176.6 * rho_otn  # K
        P_cr = 4.6 + 0.1 * rho_otn * 100  # МПа

        P_pr = P_MPa / P_cr
        T_pr = T_K / T_cr

        if method == 'latonov':
            # Метод Латонова-Гуревича
            z = 1 - 0.023 * P_pr + 0.02 * P_pr ** 2 - 0.001 * P_pr ** 3
            z = z * (1 + 0.02 * (T_pr - 1.5))
        elif method == 'brown':
            # Аппроксимация Брауна-Катца
            a1 = 0.31506237
            a2 = -1.0467099
            a3 = -0.57832729
            a4 = 0.53530771
            a5 = -0.61232032
            a6 = -0.10488813
            a7 = 0.68157001
            a8 = 0.68446549

            z = (a1 + a2 / T_pr + a3 / T_pr ** 3 + a4 / T_pr ** 4 + a5 / T_pr ** 5) * P_pr + \
                (a6 + a7 / T_pr + a8 / T_pr ** 3) * P_pr ** 2
            z = 1 + z
        else:
            # Полиномиальная аппроксимация (упрощенная)
            z = 1 - 0.023 * P_pr + 0.02 * P_pr ** 2 - 0.001 * P_pr ** 3
            z = z * (1 + 0.02 * (T_pr - 1.5))

        # Ограничения
        z = max(0.5, min(z, 1.2))

        return z

    @staticmethod
    def viscosity(P_MPa, T_K, rho_otn):
        """
        Расчет вязкости газа (метод Ли и др.)

        Возвращает вязкость в сПз
        """
        M_air = 28.96
        M_gas = M_air * rho_otn

        T_cr = 92.2 + 176.6 * rho_otn
        P_cr = 4.6 + 0.1 * rho_otn * 100

        P_pr = P_MPa / P_cr
        T_pr = T_K / T_cr

        K = (9.4 + 0.02 * M_gas) * T_K ** 1.5 / (209.2 + 19.26 * M_gas + T_K)
        X = 3.5 + 986 / T_K + 0.01 * M_gas
        Y = 2.4 - 0.2 * X

        mu_1 = K * np.exp(X * (rho_otn ** Y))
        mu = mu_1 * (1 + 0.5 * P_pr / (1 + P_pr))

        return mu

    @staticmethod
    def Bg(P_MPa, T_K, z):
        """Объемный коэффициент газа (м³/м³)"""
        P_st = 0.101325  # МПа
        T_st = 293.15    # K

        return (P_st / P_MPa) * (T_K / T_st) * z

    @staticmethod
    def density(P_MPa, T_K, rho_otn, z):
        """Плотность газа (кг/м³)"""
        rho_air = 1.293  # кг/м³ при н.у.
        return rho_otn * rho_air * (P_MPa / 0.101325) * (293.15 / T_K) / z
