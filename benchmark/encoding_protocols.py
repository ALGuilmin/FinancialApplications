"""
This module contains a class for selecting data encoding protocols

Authors: Alberto Pedro Manzano Herrero & Gonzalo Ferro

"""

import sys
sys.path.append("../")
import numpy as np
import qat.lang.AQASM as qlm
import QQuantLib.DL.data_loading as dl
from QQuantLib.utils.utils import test_bins

class Encoding:

    """
    Class for data encoding into the quantum circuit.

    """
    def __init__(self, array_function, array_probability=None, encoding=None, **kwargs):
        """
        Initialize class for data encoding into the quantum circuit.

        Parameters
        ----------

        array_function : numpy array
            numpy array wiht the desired function for encoding into the
            Quantum Cirucit:
                * MANDATORY of lenght = 2^n
                * MANDATORY: max(array_function) <= 1.0.
        array_probability : numpy array
            numpy array wiht the desired probability for encoding into the
            Quantum Cirucit:
                * Is None is provided uniform distribution will be used
                * MANDATORY of lenght = 2^n
                * MANDATORY: sum(array_probability) <= 1.0.
                * MANDATORY: length(array_function) == length(array_probability)
        encoding : int
            Selecting the encode protocol
                * 0 : standard encoding procedure (load density as density)
                * 1 : first encoding procedure (load density as function)
                * 2 : second encoding procedure (double loading of a density as a density)
        kwargs : dictionary
        """
        #Inputs arrays MUST be of length 2^n
        self.n_qbits = test_bins(array_function)
        self.function = array_function
        if np.max(self.function) > 1.00:
            raise ValueError("array_function not properly normalised.\
            Please divdide by the max(array_function)")
        if array_probability is not None:
            qbits_prob = test_bins(array_probability)
            if self.n_qbits != qbits_prob:
                raise ValueError("Lengths of array_function and \
                array_probability MUST BE equal")
            if np.sum(array_probability) > 1.00:
                raise ValueError("array_function not properly normalised.\
                Please divdide by the sum(array_probability)")
        self.probability = array_probability
        self.encoding = encoding

        self.kwargs = kwargs
        self.multiplexor_bool = self.kwargs.get("multiplexor", True)
        if self.multiplexor_bool:
            self.multiplexor = "multiplexor"
        else:
            self.multiplexor = "brute_force"


        self.oracle = None
        self.p_gate = None
        self.function_gate = None
        self.co_target = None
        self.co_index = None
        self.registers = None

    def reset(self):
        """
        Method for resetting atributes
        """
        self.oracle = None
        self.p_gate = None
        self.function_gate = None
        self.co_target = None
        self.co_index = None
        self.registers = None

    def oracle_encoding_01(self):
        """
        Method for creating the oracle. The probability density will be
        loaded with proability density gate and the
        function will be loaded as function array.
        """

        self.reset()
        self.oracle = qlm.QRoutine()
        # Creation of probability loading gate
        if self.probability is not None:
            self.p_gate = dl.load_probability(
                self.probability,
                method=self.multiplexor
            )
        else:
            self.p_gate = dl.uniform_distribution(self.n_qbits)

        # Creation of function loading gate
        self.function_gate = dl.load_array(
            np.sqrt(self.function), id_name="Function", method=self.multiplexor)
        self.registers = self.oracle.new_wires(self.function_gate.arity)
        # Step 1 of Procedure: apply loading probabilty gate
        self.oracle.apply(self.p_gate, self.registers[: self.p_gate.arity])
        # Step 2 of Procedure: apply loading function gate
        self.oracle.apply(self.function_gate, self.registers)
        self.co_target = [0]
        self.co_index = [self.oracle.arity - 1]

    def oracle_encoding_02(self):
        """
        Method for creating the oracle. The probability density and the
        payoff functions will be loaded as function arrays.
        """
        self.reset()
        self.oracle = qlm.QRoutine()
        # For new data loading procedure we need n+2 qbits
        if self.probability is None:
            raise ValueError("For type encoding 2 array_probability \
            CAN NOT BE NONE")
        self.registers = self.oracle.new_wires(self.n_qbits + 2)
        # Step 2 of Procedure: apply Uniform distribution
        self.oracle.apply(
            dl.uniform_distribution(self.n_qbits), self.registers[: self.n_qbits]
        )
        # Step 3 of Procedure: apply loading function operator for loading p(x)
        self.p_gate = dl.load_array(
            self.probability,
            id_name="Probability",
            method=self.multiplexor
        )
        self.oracle.apply(
            self.p_gate, [self.registers[: self.n_qbits], self.registers[self.n_qbits]]
        )
        # Step 5 of Procedure: apply loading function operator for loading f(x)
        self.function_gate = dl.load_array(
            self.function,
            id_name="Function",
            method=self.multiplexor
        )
        self.oracle.apply(
            self.function_gate,
            [self.registers[: self.n_qbits], self.registers[self.n_qbits + 1]],
        )
        # Step 7 of Procedure: apply Uniform distribution
        self.oracle.apply(
            dl.uniform_distribution(self.n_qbits), self.registers[: self.n_qbits]
        )
        self.co_target = [0 for i in range(self.oracle.arity)]
        self.co_index = [i for i in range(self.oracle.arity)]

    def oracle_encoding_03(self):
        """
        Method for creating the oracle. The probability density and the
        payoff functions will be loaded as function arrays.
        """
        self.reset()
        self.oracle = qlm.QRoutine()
        # Creation of probability loading gate
        if self.probability is not None:
            self.p_gate = dl.load_probability(
                self.probability,
                id_name="Probability",
                method=self.multiplexor
            )
        else:
            self.p_gate = dl.uniform_distribution(self.n_qbits)
        # Creation of function loading gate
        self.function_gate = dl.load_array(
            self.function,
            id_name="Function",
            method=self.multiplexor
            )
        self.registers = self.oracle.new_wires(self.function_gate.arity)
        # Step 1 of Procedure: apply loading probabilty gate
        self.oracle.apply(self.p_gate, self.registers[: self.p_gate.arity])
        # Step 2 of Procedure: apply loading function gate
        self.oracle.apply(self.function_gate, self.registers)
        # Step 3 of Procedure: apply loading probability gate
        self.oracle.apply(self.p_gate.dag(), self.registers[: self.p_gate.arity])
        self.co_target = [0 for i in range(self.oracle.arity)]
        self.co_index = [i for i in range(self.oracle.arity)]


    def run(self):
        if self.encoding is None:
            raise ValueError("Encoding parameter MUST NOT BE None. \
            Please select 0,1 or 2 for encoding procedure!")
        if self.encoding == 0:
            self.oracle_encoding_01()
        elif self.encoding == 1:
            self.oracle_encoding_02()
        elif self.encoding == 2:
            self.oracle_encoding_03()
        else:
            raise ValueError("Poblem with encoding atribute!")

