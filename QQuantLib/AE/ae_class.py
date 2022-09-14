"""
This module contains a general class for solving AE problems
using the algorithm classes from QQuantLib.AE library package
Authors: Alberto Pedro Manzano Herrero & Gonzalo Ferro

"""

import pandas as pd
from qat.qpus import get_default_qpu
from QQuantLib.AE.maximum_likelihood_ae import MLAE
from QQuantLib.AE.ae_classical_qpe import CQPEAE
from QQuantLib.AE.ae_iterative_quantum_pe import IQPEAE
from QQuantLib.AE.iterative_quantum_ae import IQAE
from QQuantLib.AE.real_quantum_ae import RQAE
from QQuantLib.utils.utils import text_is_none

class AE:
    """
    Class for creating and solving an AE problem
    """
    def __init__(self, oracle=None, target=None, index=None, ae_type=None, **kwargs):
        """

        Method for initializing the class

        Parameters
        ----------
        oracle: QLM gate
            QLM gate with the Oracle for implementing the
            Grover operator
        target : list of ints
            python list with the target for the amplitude estimation
        index : list of ints
            qubits which mark the register to do the amplitude
            estimation
        ae_type : string
            string with the desired AE algorithm:
            MLAE, CQPEAE, IQPEAE, IQAE, RQAE
        kwars : dictionary
            dictionary that allows the configuration of the AE algorithm:
            Implemented keys: different keys from the different AE algorithms
            can be provided.
        """

        # Setting attributes
        text_is_none(oracle, "oracle", variable_type="QLM Routine")
        self.oracle = oracle
        text_is_none(target, "target", variable_type=list)
        self.target = target
        text_is_none(index, "index", variable_type=list)
        self.index = index

        #Proccesing kwargs
        self.kwargs = kwargs
        self.linalg_qpu = self.kwargs.get("qpu", None)
        if self.linalg_qpu is None:
            print("Not QPU was provide. Default QPU will be used")
            self.linalg_qpu = get_default_qpu()
        self._ae_type = ae_type
        #atributtes created
        self.solver_ae = None
        self.ae_pdf = None
        self.solver_dict = None

    @property
    def ae_type(self):
        """
        creating ae_type property
        """
        return self._ae_type

    @ae_type.setter
    def ae_type(self, stringvalue):
        """
        setter of the target property
        """
        self._ae_type = stringvalue
        self.solver_ae = None
        self.ae_pdf = None

    def create_ae_solver(self):
        """
        Method for instantiate the AE algorithm class.
        """
        text_is_none(self.ae_type, "ae_type atribute", variable_type=str)
        #commom ae settings
        self.solver_dict = {
            "mcz_qlm" : self.kwargs.get("mcz_qlm", True),
            "qpu" : self.kwargs.get("qpu", None)
        }


        if self.ae_type == "MLAE":
            for par in ["delta", "ns", "schedule"]:
                val_par = self.kwargs.get(par)
                if val_par is not None:
                    self.solver_dict.update({par : val_par})
            #    "delta" : self.kwargs.get("delta", None),
            #    "ns" : self.kwargs.get("ns", None),
            #    "schedule" : self.kwargs.get("schedule", None)
            #})
            self.solver_ae = MLAE(
                self.oracle,
                target=self.target,
                index=self.index,
                **self.solver_dict
            )
        elif self.ae_type == "CQPEAE":
            for par in ["auxiliar_qbits_number", "shots"]:
                val_par = self.kwargs.get(par)
                if val_par is not None:
                    self.solver_dict.update({par : val_par})
            #self.solver_dict.update({
            #    "auxiliar_qbits_number" : self.kwargs.get(
            #        "auxiliar_qbits_number", None),
            #    "shots" : self.kwargs.get("shots", None)
            #})
            self.solver_ae = CQPEAE(
                self.oracle,
                target=self.target,
                index=self.index,
                **self.solver_dict
            )
        elif self.ae_type == "IQPEAE":
            for par in ["cbits_number", "shots"]:
                val_par = self.kwargs.get(par)
                if val_par is not None:
                    self.solver_dict.update({par : val_par})
            #self.solver_dict.update({
            #    "cbits_number" : self.kwargs.get("cbits_number", None),
            #    "shots" : self.kwargs.get("shots", None)
            #})
            self.solver_ae = IQPEAE(
                self.oracle,
                target=self.target,
                index=self.index,
                **self.solver_dict
            )
        elif self.ae_type == "IQAE":
            for par in ["epsilon", "alpha", "shots"]:
                val_par = self.kwargs.get(par)
                if val_par is not None:
                    self.solver_dict.update({par : val_par})
            #self.solver_dict.update({
            #    "epsilon" : self.kwargs.get("epsilon", None),
            #    "alpha" : self.kwargs.get("alpha", None),
            #    "shots" : self.kwargs.get("shots", None)
            #})
            self.solver_ae = IQAE(
                self.oracle,
                target=self.target,
                index=self.index,
                **self.solver_dict
            )
        elif self.ae_type == "RQAE":
            for par in ["epsilon", "gamma", "q"]:
                val_par = self.kwargs.get(par)
                if val_par is not None:
                    self.solver_dict.update({par : val_par})
            #self.solver_dict.update({
            #    "epsilon" : self.kwargs.get("epsilon", None),
            #    "gamma" : self.kwargs.get("gamma", None),
            #    "q" : self.kwargs.get("q", None),
            #    "shots" : self.kwargs.get("shots", None)
            #})
            self.solver_ae = RQAE(
                self.oracle,
                target=self.target,
                index=self.index,
                **self.solver_dict
            )
        else:
            raise ValueError("AE algorithm IS NOT PROVIDED in ae_type parameter \
            Please use: MLAE, CQPEAE, IQPEAE, IQAE, RQAE")
    def run(self):
        """
        Method for running an AE problem
        """
        #create AE algorithm object
        self.create_ae_solver()
        self.solver_ae.run()
        # Recover amplitude estimation from ae_solver
        self.ae_pdf = pd.DataFrame(
            [self.solver_ae.ae, self.solver_ae.ae_l, self.solver_ae.ae_u],
            index=["ae", "ae_l", "ae_u"],
        ).T
