import copy
import sys

import numpy as np

from utils import read_yaml_file, get_profs_initials, pretty_print_timetable, pretty_print_timetable_aux_zile
import heapq as hp


class State:
    def __init__(
            self,
            timetable_specs,
            sala_ore_libere,
            prof_ore_libere,
            prof_ore_maxim
    ) -> None:
        self.state = {}
        self.vars = []
        self.domains = {}
        self.cost = 0


best_solution = None
interations = 0
name = sys.argv[1]
input_file = ""
best_cost = 0
states = 0
out = None

def conflicts(state, profi_conflicte):
    '''
    Calculeaza nr de conflicte soft
    '''
    conflicte = 0
    for zi, intervale in state.items():
        for interval, sali in intervale.items():
            for sala, ocupare in sali.items():
                if ocupare != None:
                    prof = ocupare[0]
                    if zi not in profi_conflicte[prof]["zi_buna"]:
                        # print(prof + str(interval))
                        conflicte += 1
                    if zi in profi_conflicte[prof]["zi_proasta"]:
                        # print(prof + str(interval))
                        conflicte += 1
                    if interval not in profi_conflicte[prof]["ora_buna"]:
                        # print(prof + str(interval))
                        conflicte += 1
                    if interval in profi_conflicte[prof]["ora_proasta"]:
                        # print(prof + str(interval))
                        conflicte += 1
    return conflicte


def new_domain_act(domain, vars, max_cost, zi, interval, prof, sala, ore_prof):
    new_d = copy.deepcopy(domain)
    # Eliminam valorile in plus din viitoarele stari
    for info_vars in vars:
        index = 0
        info_materie = new_d[info_vars[1]]
        while index < len(info_materie):
            if info_materie[index][5] > max_cost:
                info_materie.pop(index)
            elif info_materie[index][4] == zi and info_materie[index][3] == interval and info_materie[index][
                1] == sala:
                info_materie.pop(index)
            elif (info_materie[index][4] == zi and info_materie[index][3] == interval and info_materie[index][
                2] == prof) or (info_materie[index][2] == prof and ore_prof == 0):
                info_materie.pop(index)
            else:
                index += 1
    return new_d


def PCSP(vars, domains, constraints, prof_ore_maxim, acceptable_cost, solution, cost):
    '''
        DOMAIN FORMA {Materie: (Capacitate, Sala, Prof, Interval, Zi, nr_conflicte)}
    '''

    global best_solution
    global iterations
    global best_cost
    global states
    if not vars:
        # Dacă nu mai sunt variabile, am ajuns la o soluție mai bună
        best_solution = copy.deepcopy(solution)
        best_cost = cost
        print("New best: " + str(cost))
        # raise Exception("Sorry, no numbers below zero")
        if cost <= acceptable_cost:
            return True
    else:
        while domains[vars[0][1]]:
            # Luăm prima variabilă și prima valoare din domeniu
            var = vars[0]
            val = domains[var[1]].pop(0)
            iterations += 1
            print(iterations)
            # Calculam noul cost
            new_cost = cost + val[5]
            # # Calculam noul cost
            # print("new_cost" + str(new_cost) + " best = "+str(best_cost)+" acc = " + str(acceptable_cost))
            if new_cost < best_cost and new_cost <= acceptable_cost:
                # Calculam noul vars
                new_vars = copy.deepcopy(vars)
                new_vars[0] = (new_vars[0][0] - val[0], new_vars[0][1], new_vars[0][2])
                old_mat = None
                if new_vars[0][0] <= 0:
                    old_mat = new_vars.pop(0)
                # Actualizam nr de ore ale profesorului si nr de studenti ramasi la acea materie
                new_prof_ore_maxim = copy.deepcopy(prof_ore_maxim)
                new_prof_ore_maxim[val[2]] -= 1

                # Facem noua solutie + noul domeniu
                new_solution = copy.deepcopy(solution)
                new_solution[val[4]][val[3]][val[1]] = (val[2], var[1])
                new_domain = new_domain_act(domains, new_vars, acceptable_cost - new_cost, val[4], val[3], val[2],
                                            val[1],
                                            new_prof_ore_maxim[val[2]])
                states += 1
                if old_mat is not None:
                    del new_domain[old_mat[1]]

                if PCSP(new_vars, new_domain, constraints, new_prof_ore_maxim, acceptable_cost, new_solution,
                        new_cost):
                    return True

    # Dacă nu mai sunt valori în domeniu, am terminat căutarea
    return False


def run_pcsp(vars, domains, solution, acceptable_cost, constraints, prof_ore_maxim, profi_conflicte):
    global best_solution
    global best_cost
    global iterations

    best_solution = {}
    for prof_conf in constraints.values():
        best_cost += len(prof_conf)

    iterations = 0

    if PCSP(vars, domains, constraints, prof_ore_maxim, acceptable_cost, solution, 0):
        print(f"Best found in {iterations} iterations and {states} states: {str(best_cost)}")
        print(pretty_print_timetable_aux_zile(best_solution, input_file))
    else:
        print(f"Acceptable solution not found in {iterations}; Best found: {str(best_cost)} - {str(best_solution)}")


def start_csp(input_path):
    # if __name__ == '__main__':
    # Creez tabelul cu info
    global input_file
    global out
    input_name = "inputs\\" + input_path + ".yaml"
    input_file = input_name
    out = open("output_" + input_path + ".txt", "w")
    timetable_specs = read_yaml_file(input_name)
    print(timetable_specs)
    acceptable_cost = 1
    vars = []
    domains = {}
    profi_conflicte = {}
    prof_ore_maxim = {}
    solution = {}

    # Conflicte prof
    for prof, info in timetable_specs["Profesori"].items():
        prof_ore_maxim[prof] = 7
        profi_conflicte[prof] = {"zi_buna": [], "zi_proasta": [], "ora_buna": [], "ora_proasta": []}
        for conflict in timetable_specs["Profesori"][prof]["Constrangeri"]:
            if conflict[0] != "!":
                if conflict[0].isnumeric():
                    interval = tuple(list(map(int, conflict.split("-"))))
                    for x in range(int((interval[1] - interval[0]) / 2)):
                        profi_conflicte[prof]["ora_buna"].append((2 * x + interval[0], 2 * (x + 1) + interval[0]))
                else:
                    profi_conflicte[prof]["zi_buna"].append(conflict)
            else:
                if conflict[1].isnumeric():
                    interval = tuple(list(map(int, conflict[1:].split("-"))))
                    for x in range(int((interval[1] - interval[0]) / 2)):
                        profi_conflicte[prof]["ora_proasta"].append((2 * x + interval[0], 2 * (x + 1) + interval[0]))
                else:
                    profi_conflicte[prof]["zi_proasta"].append(conflict[1:])

    for materie, nr_stud in timetable_specs["Materii"].items():
        nr_sali = 0
        for sala_info in timetable_specs["Sali"].values():
            if materie in sala_info["Materii"]:
                nr_sali += 1
        vars.append((nr_stud, materie, nr_sali))
        domains[materie] = []
    sala_prof = []
    for sala, info_sala in timetable_specs["Sali"].items():
        for materie in info_sala["Materii"]:
            for prof, prof_info in timetable_specs["Profesori"].items():
                if materie in prof_info["Materii"]:
                    sala_prof.append((info_sala["Capacitate"], sala, prof, materie))

    for zi in timetable_specs["Zile"]:
        solution[zi] = {}
        for interval in timetable_specs["Intervale"]:
            int_interval = tuple(map(int, interval.strip('()').split(',')))
            solution[zi][int_interval] = {}
            # Initializare domeniu
            for elem in sala_prof:
                # Nu adaugam tuplurile care genereaza mai mult de un conflict
                nr_conflicte = 0
                if zi not in profi_conflicte[elem[2]]["zi_buna"]:
                    nr_conflicte += 1
                if zi in profi_conflicte[elem[2]]["zi_proasta"]:
                    nr_conflicte += 1
                if int_interval not in profi_conflicte[elem[2]]["ora_buna"]:
                    nr_conflicte += 1
                if int_interval in profi_conflicte[elem[2]]["ora_proasta"]:
                    nr_conflicte += 1
                if nr_conflicte <= acceptable_cost:
                    domains[elem[3]].append((elem[0], elem[1], elem[2],
                                             int_interval, zi, nr_conflicte,
                                             len(timetable_specs["Profesori"][elem[2]]["Materii"]),
                                             len(timetable_specs["Sali"][elem[1]]["Materii"])))
            # Initializare solutie
            for sala in timetable_specs["Sali"]:
                solution[zi][int_interval][sala] = None

    for key, lista_materie in domains.items():
        domains[key] = sorted(lista_materie, key=lambda x: (x[7], x[6], -x[0]))

    vars = sorted(vars, key=lambda x: (x[2], x[0]))
    run_pcsp(vars, domains, solution, acceptable_cost, profi_conflicte, prof_ore_maxim, profi_conflicte)
