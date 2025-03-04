import sys
import random
import numpy as np

from utils import read_yaml_file, get_profs_initials, pretty_print_timetable, pretty_print_timetable_aux_zile
import heapq as hp
import copy

best_solution = None
best_total_iters = 0
best_total_states = 0
best_cost = 0
input_file = None
out = None


# def stochastic_hill_climbing(initial: State, materie_sali, profi_conflicte, rank_zi_interval, max_iters: int = 1000):
#     iters, states = 0, 0
#     curr_state = copy.deepcopy(initial)
#     while iters < max_iters:
#         iters += 1
#         next_states = curr_state.get_next_states_slot_slot(materie_sali, rank_zi_interval)
#         minim = curr_state.conflicts(profi_conflicte)
#         if len(next_states) == 0:
#             break
#         min_list = []
#         ok = 0
#         for next_state in next_states:
#             states += 1
#             next_state_conf = next_state.conflicts(profi_conflicte)
#             if next_state_conf < minim:
#                 min_list.append(next_state)
#                 ok = 1
#         # Nicio stare cu mai putine conflicte
#         if ok == 0:
#             break
#         curr_state = random.choice(min_list)
#     return curr_state.conflicts(profi_conflicte), iters, states, curr_state
#
#
# def first_choice_hill_climbing(initial: State, materie_sali, profi_conflicte, rank_zi_interval, max_iters: int = 1000):
#     iters, states = 0, 0
#     curr_state = copy.deepcopy(initial)
#     while iters < max_iters:
#         iters += 1
#         next_states = curr_state.get_next_states_slot_slot(materie_sali, rank_zi_interval)
#         minim = curr_state.conflicts(profi_conflicte)
#         # if len(next_states) == 0:
#         #     break
#         min_state = None
#         ok = 0
#         for next_state in next_states:
#             states += 1
#             next_state_conf = next_state.conflicts(profi_conflicte)
#             if next_state_conf < minim:
#                 print("new conflicts = " + str(next_state_conf))
#                 min_state = next_state
#                 ok = 1
#                 break
#         # Nicio stare cu mai putine conflicte
#         if ok == 0:
#             break
#         curr_state = min_state
#     return curr_state.conflicts(profi_conflicte), iters, states, curr_state


def nr_conflicte_prof_interval(zi, int_interval, prof, profi_conflicte):
    nr_conflicte = 0
    if zi not in profi_conflicte[prof]["zi_buna"]:
        nr_conflicte += 1
    if zi in profi_conflicte[prof]["zi_proasta"]:
        nr_conflicte += 1
    if int_interval not in profi_conflicte[prof]["ora_buna"]:
        nr_conflicte += 1
    if int_interval in profi_conflicte[prof]["ora_proasta"]:
        nr_conflicte += 1
    return nr_conflicte


def weight_list_calc(lista, profi_conflicte):
    lista_weight = []
    nr_total_conflicte = 0

    # Calculez numarul total de conflicte pentru fiecare pereche
    for elem in lista:
        sala = elem[0]
        prof = elem[1]
        for zi_ora in elem[2]:
            zi = zi_ora[0]
            interval = zi_ora[1]
            nr_conflicte = nr_conflicte_prof_interval(zi, interval, prof, profi_conflicte)
            nr_total_conflicte += nr_conflicte

            lista_weight.append(((sala, prof, zi_ora, nr_conflicte), nr_conflicte))

    # Normalizam ponderea
    lista_weight = [(elem, 1 - (nr_conflicte / (nr_total_conflicte + 1))) for elem, nr_conflicte in lista_weight]
    return zip(*lista_weight)


class State:
    def __init__(
            self,
            timetable_specs,
            sala_ore_libere,
            prof_ore_libere,
            prof_ore_maxim
    ) -> None:
        self.nr_conflicte = 0
        self.state = {}
        self.sala_ore_libere = sala_ore_libere
        self.prof_ore_libere = prof_ore_libere
        self.prof_ore_maxim = prof_ore_maxim

        for zi in timetable_specs["Zile"]:
            self.state[zi] = {}
            for interval in timetable_specs["Intervale"]:
                int_interval = tuple(map(int, interval.strip('()').split(',')))
                self.state[zi][int_interval] = {}
                for prof in timetable_specs["Profesori"]:
                    # zi_int = zi + "," + interval
                    self.prof_ore_libere[prof].append((zi, int_interval))
                for sala in timetable_specs["Sali"]:
                    # zi_int = zi + "," + interval
                    self.state[zi][int_interval][sala] = None
                    self.sala_ore_libere[sala].append((zi, int_interval))

    def initial_state_gen(self, queue_materie, materie_sali, mat_profi, profi_conflicte, timetable_specs):
        while len(queue_materie) != 0:
            elem = queue_materie.pop(0)
            nr = elem[0]
            materie = elem[1]
            list_sala_prof = []
            # cautam toate intersectiile de intervale comune dintre un prof si o sala potrivita pentru
            # aceasta materie
            for sala in materie_sali[materie]:
                for prof in mat_profi[materie]:
                    # Profu are mai putin de 7 intervale
                    if self.prof_ore_maxim[prof] > 0:
                        intersectie = list(
                            filter(lambda t: t in self.sala_ore_libere[sala], self.prof_ore_libere[prof]))
                        if len(intersectie) != 0:
                            list_sala_prof.append((sala, prof, intersectie))
            # alegem random o sala, un prof si un interval
            if len(list_sala_prof) == 0:
                return False

            list_sala_prof, ponderi = weight_list_calc(list_sala_prof, profi_conflicte)
            element_ales = random.choices(list_sala_prof, weights=ponderi)[0]
            sala = element_ales[0]
            prof = element_ales[1]
            zi_ora = element_ales[2]
            nr_conflicte = element_ales[3]

            # Stergem ora si ziua din tabela cu sali si profesori
            self.prof_ore_libere[prof].remove(zi_ora)
            self.sala_ore_libere[sala].remove(zi_ora)

            # Scadem nr de intervale ale profului
            self.prof_ore_maxim[prof] -= 1

            zi = zi_ora[0]
            interval = zi_ora[1]

            # Adaugam in tabela si actualizam nr de conflicte
            self.state[zi][interval][sala] = (prof, materie)
            self.nr_conflicte += nr_conflicte

            # Verificam daca trebuie adaugata inapoi materia, mai avand inca studenti nerepartizati
            nr -= timetable_specs["Sali"][sala]["Capacitate"]
            if nr > 0:
                queue_materie.insert(0, (nr, materie))
        return True

    def aux_get_next_states_old_state_is_not_None(self, timetable_specs, materie_sali, old_zi, old_interval, old_sala,
                                                  old_ocupare,
                                                  new_zi,
                                                  new_interval,
                                                  profi_conflicte):
        new_states = []
        old_prof = old_ocupare[0]
        materie = old_ocupare[1]

        # Iau fiecare sala in care se poate tine materia din vechiul slot
        for new_sala in materie_sali[materie]:
            new_ocupare = self.state[new_zi][new_interval][new_sala]
            # Verificam daca in noua sala se preda o materie care poate fi predata si in vechia
            # sala
            if new_ocupare is not None and old_sala not in materie_sali[new_ocupare[1]]:
                continue

            # Verificam daca proful din noua sala are intervalul vechi ocupat
            if new_ocupare is not None and (old_zi, old_interval) not in self.prof_ore_libere[new_ocupare[0]]:
                continue

            # Calculam nr de conflicte pentru vechiul slot
            old_slot_conflicte_old_slot = nr_conflicte_prof_interval(old_zi, old_interval, old_prof,
                                                                     profi_conflicte)
            old_slot_conflicte_new_slot = nr_conflicte_prof_interval(new_zi, new_interval,
                                                                     old_prof,
                                                                     profi_conflicte)
            # Calculam nr de conflicte pentru noul slot
            new_slot_conflicte_new_slot = 0
            new_slot_conflicte_old_slot = 0
            if new_ocupare is not None:
                new_slot_conflicte_new_slot = nr_conflicte_prof_interval(new_zi, new_interval,
                                                                         new_ocupare[0],
                                                                         profi_conflicte)
                new_slot_conflicte_old_slot = nr_conflicte_prof_interval(old_zi, old_interval,
                                                                         new_ocupare[0],
                                                                         profi_conflicte)

            # Verificam daca noua stare ar avea un nr de conflicte mai mic decat vechia stare
            if (old_slot_conflicte_old_slot + new_slot_conflicte_new_slot) <= (
                    old_slot_conflicte_new_slot +
                    new_slot_conflicte_old_slot):
                continue

            new_state = copy.deepcopy(self)

            # Actualizam nr de conflicte
            new_state.nr_conflicte -= new_slot_conflicte_new_slot - old_slot_conflicte_old_slot
            new_state.nr_conflicte += new_slot_conflicte_old_slot + old_slot_conflicte_new_slot

            # Adaugam old_slotul al profului si il stergem pe new_slot din orele libere
            new_state.prof_ore_libere[old_prof].append((old_zi, old_interval))
            new_state.prof_ore_libere[old_prof].remove((new_zi, new_interval))

            # Adaugam new_slotul al profului si il eliminam pe old_slot daca este cazul din ore
            # libere
            if new_ocupare is not None:
                new_state.prof_ore_libere[new_ocupare[0]].append((new_zi, new_interval))
                new_state.prof_ore_libere[new_ocupare[0]].remove((old_zi, old_interval))

            # Actualizam sloturile salilor old si new daca este cazul
            # Se face doar in cazul in care new slot e None
            if new_ocupare is None:
                new_state.sala_ore_libere[old_sala].append((old_zi, old_interval))
                new_state.sala_ore_libere[new_sala].remove((new_zi, new_interval))

            # Actualizam tabelul
            new_state.state[new_zi][new_interval][new_sala] = old_ocupare
            new_state.state[old_zi][old_interval][old_sala] = new_ocupare

            # Adaugam noua stare in lista
            new_states.append(new_state)

        return new_states

    def aux_get_next_states_old_state_is_None(self, timetable_specs, old_zi, old_interval, old_sala, new_zi,
                                              new_interval, profi_conflicte, materie_sali):
        new_states = []
        # Iau fiecare sala din acest interval
        for new_sala in timetable_specs["Sali"]:
            if self.state[new_zi][new_interval][new_sala] is None:
                continue
            new_ocupare = self.state[new_zi][new_interval][new_sala]
            # Verificam daca in noua sala se preda o materie care poate fi predata si in vechia
            # sala
            if old_sala not in materie_sali[new_ocupare[1]]:
                continue
            # Verificam daca proful din noua sala are intervalul vechi ocupat
            if (old_zi, old_interval) not in self.prof_ore_libere[new_ocupare[0]]:
                continue

            # Calculam nr de conflicte pentru noul slot
            new_slot_conflicte_new_slot = nr_conflicte_prof_interval(new_zi, new_interval,
                                                                     new_ocupare[0],
                                                                     profi_conflicte)
            new_slot_conflicte_old_slot = nr_conflicte_prof_interval(old_zi, old_interval,
                                                                     new_ocupare[0],
                                                                     profi_conflicte)

            # Verificam daca noua schimbare are mai putine conflicte
            if new_slot_conflicte_old_slot >= new_slot_conflicte_new_slot:
                continue

            new_state = copy.deepcopy(self)

            # Actualizam nr de conflicte
            new_state.nr_conflicte = new_state.nr_conflicte - new_slot_conflicte_new_slot + new_slot_conflicte_old_slot

            # Adaugam new_slotul al profului si il eliminam pe old_slot daca este cazul din ore
            # libere
            new_state.prof_ore_libere[new_ocupare[0]].append((new_zi, new_interval))
            new_state.prof_ore_libere[new_ocupare[0]].remove((old_zi, old_interval))

            # Actualizam sloturile salilor old si new
            new_state.sala_ore_libere[old_sala].remove((old_zi, old_interval))
            new_state.sala_ore_libere[new_sala].append((new_zi, new_interval))

            # Actualizam tabelul
            new_state.state[new_zi][new_interval][new_sala] = None
            new_state.state[old_zi][old_interval][old_sala] = new_ocupare

            # Adaugam noua stare in lista
            new_states.append(new_state)

        return new_states

    def get_next_states_slot_slot(self, profi_conflicte, timetable_specs, materie_sali,
                                  rank_zi_interval):
        '''
            Intoarcem toate posibilele stari urmatoare
        '''
        next_states = []
        for old_zi, old_intervale in self.state.items():
            for old_interval, old_sali in old_intervale.items():
                for old_sala, old_ocupare in old_sali.items():

                    for new_zi, new_intervale in self.state.items():
                        for new_interval, new_sali in new_intervale.items():
                            # Verificam daca este un interval pe care l am verificat deja
                            if rank_zi_interval[new_zi][new_interval] < rank_zi_interval[old_zi][old_interval]:
                                continue
                            # Verificam daca intervalul este un interval liber pentru old_prof
                            if (old_ocupare is not None and (new_zi, new_interval) not in
                                    self.prof_ore_libere[old_ocupare[0]]):
                                continue

                            if old_ocupare is not None:
                                new_states = self.aux_get_next_states_old_state_is_not_None(timetable_specs,
                                                                                            materie_sali, old_zi,
                                                                                            old_interval, old_sala,
                                                                                            old_ocupare, new_zi,
                                                                                            new_interval,
                                                                                            profi_conflicte)
                                next_states += new_states
                            else:
                                new_states = self.aux_get_next_states_old_state_is_None(timetable_specs, old_zi,
                                                                                        old_interval, old_sala, new_zi,
                                                                                        new_interval, profi_conflicte,
                                                                                        materie_sali)
                                next_states += new_states
        return next_states

    def get_next_states_prof_slot(self, timetable_specs, profi_conflicte):
        next_states = []
        # Iau fiecare profesor de pe tușă care mai are ore libere si incerc sa l schimb in sloturi
        for new_prof, nr_ore in self.prof_ore_maxim.items():
            # Verific daca si a atins nr maxim de ore
            if nr_ore == 0:
                continue

            # Iau fiecare interval liber al acestuia
            for zi_ora in self.prof_ore_libere[new_prof]:
                zi = zi_ora[0]
                interval = zi_ora[1]
                # Verific fiecare sala ocupata
                for sala, sala_info in self.state[zi][interval].items():
                    if sala_info is None:
                        continue
                    # Verific daca materia care se preda in sala o poate preda profesorul
                    if sala_info[1] not in timetable_specs["Profesori"][new_prof]["Materii"]:
                        continue
                    old_prof = sala_info[0]
                    materie = sala_info[1]

                    # Calculam nr de conflicte si verificam daca are rost sa adaugam aceasta stare
                    new_prof_conflicte = nr_conflicte_prof_interval(zi, interval, new_prof, profi_conflicte)
                    old_prof_conflicte = nr_conflicte_prof_interval(zi, interval, old_prof, profi_conflicte)
                    if old_prof_conflicte <= new_prof_conflicte:
                        continue

                    new_state = copy.deepcopy(self)

                    # Eliminam slotul de la noul profesor si il adaugam la vechiul profesor la ore libere
                    new_state.prof_ore_libere[old_prof].append((zi, interval))
                    new_state.prof_ore_libere[new_prof].remove((zi, interval))

                    # Actualizam nr de conflicte
                    new_state.nr_conflicte = new_state.nr_conflicte - old_prof_conflicte + new_prof_conflicte

                    # Actualizam tabelul
                    new_state.state[zi][interval][sala] = (new_prof, materie)

                    # Adaugam noua stare in lista de stari
                    next_states.append(new_state)

        return next_states

    def conflicts(self, profi_conflicte):
        '''
        Calculeaza nr de conflicte soft
        '''
        conflicte = 0
        for zi, intervale in self.state.items():
            for interval, sali in intervale.items():
                for sala, ocupare in sali.items():
                    if ocupare != None:
                        prof = ocupare[0]
                        if zi not in profi_conflicte[prof]["zi_buna"]:
                            conflicte += 1
                        if zi in profi_conflicte[prof]["zi_proasta"]:
                            conflicte += 1
                        if interval not in profi_conflicte[prof]["ora_buna"]:
                            conflicte += 1
                        if interval in profi_conflicte[prof]["ora_proasta"]:
                            conflicte += 1
        return conflicte


def hill_climbing_slot_slot(timetable_specs, initial: State, materie_sali, profi_conflicte,
                            rank_zi_interval,
                            max_iters: int = 100):
    iters, states = 0, 0
    current_state = copy.deepcopy(initial)
    # print(pretty_print_timetable(initial.state,input_name))
    # print(initial.nr_conflicte)
    while iters < max_iters:
        iters += 1
        # print(rank_zi_interval)
        next_states = current_state.get_next_states_slot_slot(profi_conflicte, timetable_specs, materie_sali,
                                                              rank_zi_interval)
        minim = current_state.nr_conflicte
        if len(next_states) == 0:
            break
        min_state = next_states[0]
        ok = 0
        for next_state in next_states:
            states += 1
            if next_state.nr_conflicte < minim:
                min_state = next_state
                conf = next_state.nr_conflicte
                minim = next_state.nr_conflicte
                ok = 1
        # Nicio stare cu mai putine conflicte
        if ok == 0:
            break
        current_state = min_state
    return current_state.nr_conflicte, iters, states, current_state


def hill_climbing_prof_slot(profi_conflicte, timetable_specs, initial: State,
                            max_iters: int = 100):
    iters, states = 0, 0
    current_state = copy.deepcopy(initial)

    while iters < max_iters:
        iters += 1
        next_states = current_state.get_next_states_prof_slot(timetable_specs, profi_conflicte)
        minim = current_state.nr_conflicte
        if len(next_states) == 0:
            break
        min_state = next_states[0]
        ok = 0
        for next_state in next_states:
            states += 1
            if next_state.nr_conflicte < minim:
                min_state = next_state
                conf = next_state.nr_conflicte
                minim = next_state.nr_conflicte
                ok = 1
        # Nicio stare cu mai putine conflicte
        if ok == 0:
            break
        current_state = min_state
    return current_state.nr_conflicte, iters, states, current_state


def random_restart_hill_climbing(
        initial: State,
        materie_sali,
        materie_profi,
        profi_conflicte,
        timetable_specs,
        sala_ore_libere,
        prof_ore_libere,
        prof_ore_maxim,
        queue_materie,
        rank_zi_interval,
        acceptable_cost,
        local_best_cost,
        max_restarts: int = 100,
        run_max_iters: int = 100
):
    global best_solution
    global best_total_states
    global best_total_iters
    global best_cost
    best_cost = local_best_cost

    total_iters, total_states = 0, 0
    current_state = copy.deepcopy(initial)
    restarts = 0
    while restarts <= max_restarts:
        print("old conflicts = " + str(current_state.nr_conflicte))
        conflicts, iters, stas, new_state = hill_climbing_prof_slot(profi_conflicte, timetable_specs, current_state)

        total_iters += iters
        total_states += stas
        if conflicts < best_cost:
            best_cost = conflicts
            best_solution = new_state
            best_total_states = total_states
            best_total_iters = total_iters

        if conflicts <= acceptable_cost:
            return True, total_iters, total_states, new_state

        print("dupa primul Hc conflicte = " + str(new_state.nr_conflicte))

        conflicts, iters, stas, new_state = hill_climbing_slot_slot(timetable_specs, new_state,
                                                                    materie_sali,
                                                                    profi_conflicte,
                                                                    rank_zi_interval)
        total_iters += iters
        total_states += stas

        if conflicts < best_cost:
            best_cost = conflicts
            best_solution = new_state
            best_total_states = total_states
            best_total_iters = total_iters
        if conflicts <= acceptable_cost:
            best_cost = conflicts
            return True, total_iters, total_states, new_state
        print("dupa al doilea hc conflicts = " + str(new_state.nr_conflicte))

        conflicts, iters, stas, new_state = hill_climbing_prof_slot(profi_conflicte, timetable_specs, new_state)

        total_iters += iters
        total_states += stas

        if conflicts < best_cost:
            best_cost = conflicts
            best_solution = new_state
            best_total_states = total_states
            best_total_iters = total_iters
        if conflicts <= acceptable_cost:
            best_cost = conflicts
            return True, total_iters, total_states, new_state

        print("dupa al treilea hc conflicts = " + str(new_state.nr_conflicte))

        conflicts, iters, stas, new_state = hill_climbing_slot_slot(timetable_specs, new_state,
                                                                    materie_sali,
                                                                    profi_conflicte,
                                                                    rank_zi_interval)
        total_iters += iters
        total_states += stas

        if conflicts < best_cost:
            best_cost = conflicts
            best_solution = new_state
            best_total_states = total_states
            best_total_iters = total_iters
        if conflicts <= acceptable_cost:
            best_cost = conflicts
            return True, total_iters, total_states, new_state
        print("dupa al patrulea hc conflicts = " + str(new_state.nr_conflicte))

        while True:
            current_state = State(copy.deepcopy(timetable_specs),
                                  copy.deepcopy(sala_ore_libere),
                                  copy.deepcopy(prof_ore_libere),
                                  copy.deepcopy(prof_ore_maxim))

            if current_state.initial_state_gen(copy.deepcopy(queue_materie), materie_sali, materie_profi,
                                               profi_conflicte, timetable_specs):
                break
        restarts += 1
        print("restart = " + str(restarts))

    return False, total_iters, total_states, current_state


def run_test_random_hillclimbing(timetable_specs,
                                 sala_ore_libere,
                                 prof_ore_libere,
                                 prof_ore_maxim,
                                 queue_materie, materie_sali, materie_profi, profi_conflicte, rank_zi_interval,
                                 n_trials: int = 1, size: int = 8):
    '''
    Testam random_restart_hillclimbingul
    '''
    global input_file
    global output_file
    wins, fails = 0, 0
    total_iters, total_states, distance = 0, 0, 0
    acceptable_cost = 1
    init_best_cost = 0
    for prof_conf in profi_conflicte.values():
        init_best_cost += len(prof_conf)
    initials = []
    for _ in range(n_trials):
        while True:
            new_state = State(copy.deepcopy(timetable_specs),
                              copy.deepcopy(sala_ore_libere),
                              copy.deepcopy(prof_ore_libere),
                              copy.deepcopy(prof_ore_maxim))

            if new_state.initial_state_gen(copy.deepcopy(queue_materie), materie_sali, materie_profi,
                                           profi_conflicte,
                                           timetable_specs):
                break
        initials.append(new_state)
    x = 0
    for initial in initials:
        print("Test = " + str(x))

        is_final, iters, states, state = random_restart_hill_climbing(initial, materie_sali, materie_profi,
                                                                      profi_conflicte,
                                                                      copy.deepcopy(timetable_specs),
                                                                      copy.deepcopy(sala_ore_libere),
                                                                      copy.deepcopy(prof_ore_libere),
                                                                      copy.deepcopy(prof_ore_maxim),
                                                                      copy.deepcopy(queue_materie), rank_zi_interval,
                                                                      acceptable_cost, init_best_cost)

        if is_final:
            wins += 1
            total_iters += iters
            total_states += states
            print("Good solution")
            print(pretty_print_timetable(state.state, input_file))
        else:
            fails += 1
            print("Bad solution with distance = ", best_cost)
        x += 1

    padding = ' ' * (30 - len("HillClimbing"))
    win_percentage = (wins / n_trials) * 100.
    print(f"Success rate for {"HillClimbing"}: {padding}{wins} / {n_trials} ({win_percentage:.2f}%)")
    print(f"Average number of iterations (for wins): {' ':8}{(total_iters / wins):.2f}")
    print(f"Total number of states (for wins): {' ':>14}{total_states:,}")
    stat = {
        "wins": win_percentage,
        "iter": total_iters / wins,
        "nums": total_states
    }


def start_hc(input_path):
    # if __name__ == '__main__':
    # Creez tabelul cu info
    global input_file
    global out
    input_name = "inputs\\" + input_path + ".yaml"
    input_file = input_name
    out = open("output_" + input_path + ".txt","w")
    timetable_specs = read_yaml_file(input_name)

    # Tabela rank zi-interval
    rank = 0
    rank_zi_interval = {}
    for zi in timetable_specs["Zile"]:
        rank_zi_interval[zi] = {}
        for interval in timetable_specs["Intervale"]:
            int_interval = tuple(map(int, interval.strip('()').split(',')))
            rank_zi_interval[zi][int_interval] = rank
            rank += 1

    # Coada de marterii
    queue_materie = []
    for materie in timetable_specs['Materii'].keys():
        queue_materie.append((timetable_specs['Materii'][materie], materie))

    # Tabele pt fiecare materie cu salile/profi care sunt potriviti
    materie_sali = {}
    materie_profi = {}
    for materie in timetable_specs['Materii'].keys():
        materie_sali[materie] = []
        materie_profi[materie] = []

    # Tabela sali cu ore libere
    sala_ore_libere = {}
    prof_ore_libere = {}
    for sala, info in timetable_specs["Sali"].items():
        sala_ore_libere[sala] = []
        for materie in info["Materii"]:
            materie_sali[materie].append(sala)
    # Tabel constrangeri profi + tabela ore maxime per prof
    profi_conflicte = {}
    prof_ore_maxim = {}
    for prof, info in timetable_specs["Profesori"].items():
        prof_ore_libere[prof] = []
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
        for materie in info["Materii"]:
            materie_profi[materie].append(prof)

    run_test_random_hillclimbing(timetable_specs,
                                 sala_ore_libere,
                                 prof_ore_libere,
                                 prof_ore_maxim,
                                 queue_materie, materie_sali, materie_profi, profi_conflicte, rank_zi_interval)
    out.close()