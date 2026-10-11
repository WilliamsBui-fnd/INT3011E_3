import math
from pysat.card import CardEnc, EncType

class NQueensSATEncoder:
    def __init__(self, n):
        self.n = n
        self.clauses = []
        self.next_aux_var = n * n + 1
        
    def _get_var(self, row, col):
        return row * self.n + col + 1

    def encode(self, encoding_type='pairwise'):
        supported = {'pairwise', 'sequential', 'commander', 'product', 'binary'}
        if encoding_type not in supported:
            choices = ", ".join(sorted(supported))
            raise ValueError(
                f"Unsupported SAT encoding {encoding_type!r}; choose one of: {choices}"
            )
        self.clauses = []
        self.next_aux_var = self.n * self.n + 1
        
        # Bản đồ ánh xạ cấu hình từ string sang thư viện CardEnc của PySAT
        enc_map = {
            'pairwise': EncType.pairwise,
            'sequential': EncType.seqcounter,
            'binary': EncType.bitwise, # Bitwise chính là Binary Encoding
        }
        
        rows = [[self._get_var(r, c) for c in range(self.n)] for r in range(self.n)]
        cols = [[self._get_var(r, c) for r in range(self.n)] for c in range(self.n)]
        
        diags = []
        for i in range(1 - self.n, self.n):
            diag = [self._get_var(r, r - i) for r in range(self.n) if 0 <= r - i < self.n]
            if len(diag) > 1:
                diags.append(diag)
        for i in range(2 * self.n - 1):
            diag = [self._get_var(r, i - r) for r in range(self.n) if 0 <= i - r < self.n]
            if len(diag) > 1:
                diags.append(diag)

        for row in rows:
            self._exactly_one(row, encoding_type, enc_map)
        for col in cols:
            self._exactly_one(col, encoding_type, enc_map)
        for diag in diags:
            self._at_most_one(diag, encoding_type, enc_map)
            
        return self.clauses, self.next_aux_var - 1

    def _exactly_one(self, variables, encoding_type, enc_map):
        self.clauses.append(variables) 
        self._at_most_one(variables, encoding_type, enc_map)

    def _at_most_one(self, variables, encoding_type, enc_map):
        if encoding_type == 'product':
            # Hàm Product do ta tự viết vì PySAT không hỗ trợ sẵn
            self._amo_product(variables)
        elif encoding_type == 'commander':
            # Hàm Commander do ta tự viết vì PySAT không hỗ trợ sẵn
            self._amo_commander(variables)
        else:
            # GỌI TRỰC TIẾP HÀM AT-MOST-ONE TỪ PYSAT (cho pairwise, sequential, binary)
            enc_id = enc_map[encoding_type]
            cnf = CardEnc.atmost(lits=variables, bound=1, top_id=self.next_aux_var - 1, encoding=enc_id)
            for clause in cnf.clauses:
                self.clauses.append(clause)
            self.next_aux_var = max(self.next_aux_var, cnf.nv + 1)

    def _amo_commander(self, variables):
        if len(variables) <= 1: return
        if len(variables) <= 3:
            cnf = CardEnc.atmost(lits=variables, bound=1, top_id=self.next_aux_var - 1, encoding=EncType.pairwise)
            for clause in cnf.clauses: self.clauses.append(clause)
            self.next_aux_var = max(self.next_aux_var, cnf.nv + 1)
            return
            
        group_size = math.ceil(math.sqrt(len(variables)))
        groups = [variables[i:i + group_size] for i in range(0, len(variables), group_size)]
        commanders = [self.next_aux_var + i for i in range(len(groups))]
        self.next_aux_var += len(groups)
        
        # AMO cho commanders (dùng pairwise)
        cnf_cmd = CardEnc.atmost(lits=commanders, bound=1, top_id=self.next_aux_var - 1, encoding=EncType.pairwise)
        for clause in cnf_cmd.clauses: self.clauses.append(clause)
        self.next_aux_var = max(self.next_aux_var, cnf_cmd.nv + 1)
        
        for i, group in enumerate(groups):
            # AMO cho group (dùng pairwise)
            cnf_g = CardEnc.atmost(lits=group, bound=1, top_id=self.next_aux_var - 1, encoding=EncType.pairwise)
            for clause in cnf_g.clauses: self.clauses.append(clause)
            self.next_aux_var = max(self.next_aux_var, cnf_g.nv + 1)
            
            # Chỉ huy đúng -> Tồn tại một lính đúng (ALO cho group + -commander)
            self.clauses.append(group + [-commanders[i]])
            
            # Bất kỳ lính nào đúng -> Chỉ huy đúng
            for var in group:
                self.clauses.append([-var, commanders[i]])

    def _amo_product(self, variables):
        if len(variables) <= 1: return
        if len(variables) <= 4:
            cnf = CardEnc.atmost(lits=variables, bound=1, top_id=self.next_aux_var - 1, encoding=EncType.pairwise)
            for clause in cnf.clauses: self.clauses.append(clause)
            self.next_aux_var = max(self.next_aux_var, cnf.nv + 1)
            return
            
        p = math.ceil(math.sqrt(len(variables)))
        q = math.ceil(len(variables) / p)
        
        rows = [self.next_aux_var + i for i in range(p)]
        self.next_aux_var += p
        cols = [self.next_aux_var + i for i in range(q)]
        self.next_aux_var += q
        
        cnf_r = CardEnc.atmost(lits=rows, bound=1, top_id=self.next_aux_var - 1, encoding=EncType.pairwise)
        for clause in cnf_r.clauses: self.clauses.append(clause)
        self.next_aux_var = max(self.next_aux_var, cnf_r.nv + 1)
            
        cnf_c = CardEnc.atmost(lits=cols, bound=1, top_id=self.next_aux_var - 1, encoding=EncType.pairwise)
        for clause in cnf_c.clauses: self.clauses.append(clause)
        self.next_aux_var = max(self.next_aux_var, cnf_c.nv + 1)
        
        idx = 0
        for r in rows:
            for c in cols:
                if idx < len(variables):
                    self.clauses.append([-variables[idx], r])
                    self.clauses.append([-variables[idx], c])
                    idx += 1
                else:
                    break
