import math


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
            Метод расчета ('latonov', 'brown')
        """
        # Критические параметры
        T_cr = 92.2 + 176.6 * rho_otn
        P_cr = 4.6 + 0.1 * rho_otn * 100

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
            z = 1 - 0.023 * P_pr + 0.02 * P_pr ** 2 - 0.001 * P_pr ** 3
            z = z * (1 + 0.02 * (T_pr - 1.5))

        # Ограничения
        z = max(0.5, min(z, 1.2))
        return z

    @staticmethod
    def density(P_MPa, T_K, rho_otn, z):
        """Плотность газа (кг/м³)"""
        rho_air = 1.293
        return rho_otn * rho_air * (P_MPa / 0.101325) * (293.15 / T_K) / z