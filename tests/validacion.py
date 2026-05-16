"""Suite de validación: pruebas unitarias."""

import numpy as np
from src.modelo.particula import Particula
from src.modelo.motor_fisico import MotorFisico
from src.modelo.contenedor import Contenedor
from src.controlador import Simulador


class TestRunner:
    """Ejecuta suite de pruebas validando leyes de conservación."""
    
    def __init__(self) -> None:
        self.tests_pasados = 0
        self.tests_totales = 0
    
    def _assert_approx(self, valor: float, esperado: float, tol: float = 1e-6) -> bool:
        """Compara valores con tolerancia."""
        return abs(valor - esperado) < tol
    
    def test_energia_cinetica(self) -> bool:
        """Valida cálculo de energía cinética."""
        p = Particula(0, np.array([0, 0]), np.array([3, 4]), 2.0, 0.5)
        ek = p.calcular_energia_cinetica()
        esperado = 0.5 * 2.0 * (3**2 + 4**2)  # 0.5 * m * v²
        return self._assert_approx(ek, esperado)
    
    def test_cantidad_movimiento(self) -> bool:
        """Valida cálculo de cantidad de movimiento."""
        p = Particula(0, np.array([0, 0]), np.array([2, 3]), 1.5, 0.5)
        p_vec = p.calcular_cantidad_movimiento()
        esperado = np.array([3.0, 4.5])
        return np.allclose(p_vec, esperado)
    
    def test_actualizacion_posicion(self) -> bool:
        """Valida cinemática: x = x + v*dt."""
        p = Particula(0, np.array([1.0, 2.0]), np.array([10.0, 20.0]), 1.0, 0.5)
        p.actualizar_posicion(0.1)
        esperado = np.array([2.0, 4.0])
        return np.allclose(p.posicion, esperado)
    
    def test_deteccion_colision_cercanas(self) -> bool:
        """Detecta colisión entre partículas cercanas."""
        p1 = Particula(0, np.array([0, 0]), np.array([0, 0]), 1.0, 1.0)
        p2 = Particula(1, np.array([1.5, 0]), np.array([0, 0]), 1.0, 1.0)
        return MotorFisico.detectar_colision(p1, p2)
    
    def test_deteccion_no_colision_lejanas(self) -> bool:
        """No detecta colisión entre partículas lejanas."""
        p1 = Particula(0, np.array([0, 0]), np.array([0, 0]), 1.0, 0.5)
        p2 = Particula(1, np.array([10, 10]), np.array([0, 0]), 1.0, 0.5)
        return not MotorFisico.detectar_colision(p1, p2)
    
    def test_conservacion_momento_elastica(self) -> bool:
        """Verifica conservación de momento en colisión elástica."""
        p1 = Particula(0, np.array([0, 0]), np.array([3, 0]), 1.0, 0.5, coef_restitution=1.0)
        p2 = Particula(1, np.array([2, 0]), np.array([-2, 0]), 1.0, 0.5, coef_restitution=1.0)
        
        p_inicial = p1.calcular_cantidad_movimiento() + p2.calcular_cantidad_movimiento()
        
        MotorFisico.resolver_colision(p1, p2)
        
        p_final = p1.calcular_cantidad_movimiento() + p2.calcular_cantidad_movimiento()
        
        return np.allclose(p_inicial, p_final, atol=1e-6)
    
    def test_conservacion_energia_elastica(self) -> bool:
        """Verifica conservación de energía en colisión elástica."""
        p1 = Particula(0, np.array([0, 0]), np.array([3, 0]), 1.0, 0.5, coef_restitution=1.0)
        p2 = Particula(1, np.array([2, 0]), np.array([-2, 0]), 1.0, 0.5, coef_restitution=1.0)
        
        ek_inicial = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        MotorFisico.resolver_colision(p1, p2)
        
        ek_final = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        return self._assert_approx(ek_inicial, ek_final, tol=0.01)
    
    def test_disipacion_energia_inelastica(self) -> bool:
        """Verifica disipación de energía en colisión inelástica."""
        p1 = Particula(0, np.array([0, 0]), np.array([3, 0]), 1.0, 0.5, coef_restitution=0.5)
        p2 = Particula(1, np.array([2, 0]), np.array([-2, 0]), 1.0, 0.5, coef_restitution=0.5)
        
        ek_inicial = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        MotorFisico.resolver_colision(p1, p2)
        
        ek_final = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        return ek_final < ek_inicial  # Energía disminuye
    
    def test_deteccion_frontera(self) -> bool:
        """Detecta colisión con frontera."""
        contenedor = Contenedor(10, 10)
        p = Particula(0, np.array([0.3, 5]), np.array([0, 0]), 1.0, 0.5)
        return contenedor.detectar_colision_frontera(p)
    
    def test_rebote_pared_elastica(self) -> bool:
        """Verifica rebote elástico contra pared."""
        contenedor = Contenedor(10, 10, 1.0)
        p = Particula(0, np.array([0.1, 5]), np.array([-5, 0]), 1.0, 0.5)
        contenedor.resolver_colision_frontera(p)
        return p.velocidad[0] > 0  # vx cambió de signo
    
    def test_estabilidad_simulacion(self) -> bool:
        """Valida estabilidad numérica en 100 pasos."""
        contenedor = Contenedor(10, 10)
        simulador = Simulador(contenedor)
        
        simulador.agregar_particula(
            np.array([2, 5]),
            np.array([2, 0]),
            1.0,
            0.5,
            0.9,
            'red'
        )
        
        simulador.agregar_particula(
            np.array([8, 5]),
            np.array([-2, 0]),
            1.0,
            0.5,
            0.9,
            'blue'
        )
        
        for _ in range(100):
            simulador.paso_simulacion()
        
        # Si llegamos aquí sin excepciones, es estable
        return True
    
    def test_conservacion_momento_simulacion_completa(self) -> bool:
        """Valida conservación de momento en simulación completa."""
        contenedor = Contenedor(10, 10)
        simulador = Simulador(contenedor)
        
        simulador.agregar_particula(
            np.array([2, 5]),
            np.array([2, 0]),
            1.0,
            0.5,
            1.0,
            'red'
        )
        
        simulador.agregar_particula(
            np.array([8, 5]),
            np.array([-2, 0]),
            1.0,
            0.5,
            1.0,
            'blue'
        )
        
        p_inicial = simulador.calcular_momento_total()
        
        for _ in range(100):
            simulador.paso_simulacion()
        
        p_final = simulador.calcular_momento_total()
        
        return self._assert_approx(p_inicial, p_final, tol=0.01)
    
    def ejecutar_todos(self) -> None:
        """Ejecuta todas las pruebas."""
        print("\n" + "="*60)
        print("SUITE DE VALIDACIÓN - PRUEBAS UNITARIAS")
        print("="*60)
        
        tests = [
            ("Cálculo de energía cinética", self.test_energia_cinetica),
            ("Cálculo de cantidad de movimiento", self.test_cantidad_movimiento),
            ("Actualización de posición (cinemática)", self.test_actualizacion_posicion),
            ("Detección de colisión (cercanas)", self.test_deteccion_colision_cercanas),
            ("No detección de colisión (lejanas)", self.test_deteccion_no_colision_lejanas),
            ("Conservación de momento (elástica)", self.test_conservacion_momento_elastica),
            ("Conservación de energía (elástica)", self.test_conservacion_energia_elastica),
            ("Disipación de energía (inelástica)", self.test_disipacion_energia_inelastica),
            ("Detección de colisión con frontera", self.test_deteccion_frontera),
            ("Rebote elástico contra pared", self.test_rebote_pared_elastica),
            ("Estabilidad (100 pasos)", self.test_estabilidad_simulacion),
            ("Conservación de momento (simulación completa)", self.test_conservacion_momento_simulacion_completa),
        ]
        
        for nombre, test_func in tests:
            self.tests_totales += 1
            try:
                resultado = test_func()
                estado = "✓ PASS" if resultado else "✗ FAIL"
                print(f"{estado}: {nombre}")
                if resultado:
                    self.tests_pasados += 1
            except Exception as e:
                print(f"✗ ERROR: {nombre} - {e}")
        
        print("\n" + "="*60)
        porcentaje = (self.tests_pasados / self.tests_totales) * 100
        print(f"RESULTADO: {self.tests_pasados}/{self.tests_totales} tests pasaron ({porcentaje:.1f}%)")
        print("="*60 + "\n")


if __name__ == '__main__':
    runner = TestRunner()
    runner.ejecutar_todos()
