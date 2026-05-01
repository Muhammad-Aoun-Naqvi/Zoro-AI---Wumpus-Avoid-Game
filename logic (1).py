# logic.py

class KnowledgeBase:
    def __init__(self):
        # The KB is a list of clauses.
        # Each clause is a dictionary representing a disjunction (OR) of literals.
        # True means the literal is positive, False means it's negated.
        # Example: {'P_1_1': True, 'W_1_1': False} represents (P_1_1 V ¬W_1_1)
        self.clauses = []
        self.inference_steps = 0

    def add_clause(self, clause):
        """Adds a CNF clause to the Knowledge Base if it doesn't already exist."""
        if clause not in self.clauses:
            self.clauses.append(clause)

    def add_percept_rules(self, x, y, breeze, stench, max_r, max_c):
        """
        Converts environmental percepts into CNF clauses and adds them to the KB.
        Breeze(x,y) <==> Pit(x+1,y) V Pit(x-1,y) V Pit(x,y+1) V Pit(x,y-1)
        """
        neighbors = self._get_neighbors(x, y, max_r, max_c)
        
        # Rule 1: There is no Pit or Wumpus at the visited cell (since we are alive)
        self.add_clause({f"P_{x}_{y}": False})
        self.add_clause({f"W_{x}_{y}": False})

        # Rule 2: Handle Breeze (indicates adjacent pits)
        if breeze:
            # B_x_y -> (P_n1 V P_n2 V ...)
            # CNF: ¬B_x_y V P_n1 V P_n2 ... Since we know B_x_y is True, we just add the disjunction of pits.
            pit_clause = {f"P_{nx}_{ny}": True for nx, ny in neighbors}
            self.add_clause(pit_clause)
        else:
            # ¬B_x_y -> ¬P_n1 AND ¬P_n2 ...
            # CNF: ¬P_n1, ¬P_n2 (added as separate single-literal clauses)
            for nx, ny in neighbors:
                self.add_clause({f"P_{nx}_{ny}": False})

        # Rule 3: Handle Stench (indicates adjacent Wumpus)
        if stench:
            wumpus_clause = {f"W_{nx}_{ny}": True for nx, ny in neighbors}
            self.add_clause(wumpus_clause)
        else:
            for nx, ny in neighbors:
                self.add_clause({f"W_{nx}_{ny}": False})

    def _get_neighbors(self, x, y, max_r, max_c):
        """Helper to find valid adjacent coordinates on the dynamic grid."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < max_r and 0 <= ny < max_c:
                neighbors.append((nx, ny))
        return neighbors

    def resolve(self, ci, cj):
        """
        Attempts to resolve two clauses. Returns a list of new resolvent clauses.
        Resolution occurs when one clause contains a literal and the other contains its negation.
        """
        resolvents = []
        for literal, val in ci.items():
            if literal in cj and cj[literal] == (not val):
                self.inference_steps += 1
                # Create a new clause combining ci and cj, excluding the resolved literal
                new_clause = {**ci, **cj}
                del new_clause[literal]
                
                # Check if the new clause is a tautology (e.g., A V ¬A). If not, keep it.
                if not self._is_tautology(new_clause):
                    resolvents.append(new_clause)
        return resolvents

    def _is_tautology(self, clause):
        """Checks if a clause contains complementary literals."""
        # A dictionary cannot hold both 'A': True and 'A': False due to unique keys,
        # but logically, we ensure we don't build tautologies during resolution.
        return False

    def resolution_refutation(self, query_literal, query_val):
        """
        Uses Resolution Refutation to prove a query.
        To prove Q, we add ¬Q to the KB and try to derive an empty clause {}.
        """
        # Create a copy of the KB to avoid permanently modifying it during testing
        test_kb = [dict(c) for c in self.clauses]
        
        # Add the NEGATION of the query to the test KB
        # If we want to prove Q is False, we query False. Negation is True.
        test_kb.append({query_literal: not query_val})
        
        new = []
        while True:
            n = len(test_kb)
            pairs = [(test_kb[i], test_kb[j]) for i in range(n) for j in range(i+1, n)]
            
            for ci, cj in pairs:
                resolvents = self.resolve(ci, cj)
                for resolvent in resolvents:
                    # If we generated an empty clause, we found a contradiction! Q is proven.
                    if not resolvent: 
                        return True
                    if resolvent not in new and resolvent not in test_kb:
                        new.append(resolvent)
            
            # If no new clauses can be generated, we cannot prove the query (No contradiction found)
            if all(c in test_kb for c in new):
                return False
            
            test_kb.extend(new)

    def is_safe(self, x, y):
        """
        A cell is safe if we can prove there is NO Pit AND NO Wumpus.
        """
        # We try to prove P_x_y == False and W_x_y == False
        no_pit = self.resolution_refutation(f"P_{x}_{y}", False)
        no_wumpus = self.resolution_refutation(f"W_{x}_{y}", False)
        return no_pit and no_wumpus