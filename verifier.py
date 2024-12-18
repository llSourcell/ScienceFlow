import re
import os
import tempfile
import subprocess
from sympy import isprime

class Verifier:
    def __init__(self):
        # Check if Lean 3 is installed
        try:
            subprocess.run(['lean', '--version'], capture_output=True, check=True)
            self.lean_installed = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.lean_installed = False
            print("Warning: Lean 3 is not installed. Please install it using:\n"
                  "1. brew install elan\n"
                  "2. elan default leanprover-community/lean:3.50.3\n"
                  "3. pip install mathlibtools")

    def parse_hypothesis(self, pipeline_result: str):
        # First try to find an explicitly stated hypothesis
        pattern = r"(?:2\. Hypothesis:|Hypothesis:)(.*?)(?:\n\d\.|\Z)"
        match = re.search(pattern, pipeline_result, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # If no explicit hypothesis, try to find a Lean theorem statement
        lean_pattern = r"(?:theorem|lemma|conjecture)\s+\w+\s*\((.*?)\)\s*:"
        match = re.search(lean_pattern, pipeline_result, re.DOTALL)
        if match:
            return f"Hypothesis extracted from Lean theorem: {match.group(1)}"
        
        return None

    def extract_lean_code(self, pipeline_result: str):
        lean_blocks = []
        pattern = r"```lean\n(.*?)```"
        matches = re.finditer(pattern, pipeline_result, re.DOTALL)
        for match in matches:
            lean_blocks.append(match.group(1).strip())
        return "\n\n".join(lean_blocks)

    def verify_lean_proof(self, lean_code: str) -> str:
        if not self.lean_installed:
            return ("Lean 3 is not installed. Please install it using:\n"
                   "1. brew install elan\n"
                   "2. elan default leanprover-community/lean:3.50.3\n"
                   "3. pip install mathlibtools")

        # Check if this is an unproven conjecture
        if "sorry" in lean_code or "admitted" in lean_code or "conjecture" in lean_code:
            return "Lean Verification: This is an unproven conjecture. The formal statement has been provided but the proof is incomplete."
            
        try:
            # Create a temporary directory for the Lean project
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a basic Lean 3 project structure
                project_dir = os.path.join(temp_dir, 'temp_proof')
                os.makedirs(project_dir)
                os.makedirs(os.path.join(project_dir, 'src'))
                
                # Create leanpkg.toml
                with open(os.path.join(project_dir, 'leanpkg.toml'), 'w') as f:
                    f.write('''[package]
name = "temp_proof"
version = "0.1"
lean_version = "leanprover-community/lean:3.50.3"

[dependencies]
mathlib = {git = "https://github.com/leanprover-community/mathlib", rev = "master"}''')
                
                # Write the proof to a file
                proof_file = os.path.join(project_dir, 'src', 'main.lean')
                with open(proof_file, 'w') as f:
                    f.write(lean_code)
                
                # Try to compile the proof
                try:
                    result = subprocess.run(
                        ['lean', proof_file],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=30  # Add timeout to prevent hanging
                    )
                    
                    if result.returncode == 0:
                        return "Lean Verification: Proof successfully type-checked!"
                    else:
                        return f"Lean Verification Failed:\n{result.stderr}"
                except subprocess.TimeoutExpired:
                    return "Lean Verification: Proof checking timed out after 30 seconds"
                except subprocess.CalledProcessError as e:
                    return f"Lean Compilation Error: {e.stderr}"
                
        except Exception as e:
            return f"Lean Verification Error: {str(e)}"

    def test_collatz_sequence(self, hypothesis: str, limit=100):
        """Test the modified Collatz sequence for the first n numbers"""
        def modified_collatz(n):
            if n % 2 == 0:
                return n // 2
            return 5 * n + 1

        results = []
        for start in range(1, limit + 1):
            n = start
            sequence = [n]
            seen = {n}
            while n != 1 and len(sequence) < 1000:  # Prevent infinite loops
                n = modified_collatz(n)
                sequence.append(n)
                if n in seen:
                    results.append(f"Found cycle for {start}: {sequence}")
                    break
                seen.add(n)
                if n == 1:
                    results.append(f"Sequence for {start} reaches 1 in {len(sequence)} steps")
                    break
            if len(sequence) >= 1000:
                results.append(f"Sequence for {start} exceeds 1000 terms")

        return "\n".join(results[:5]) + "\n..." if len(results) > 5 else "\n".join(results)

    def test_prime_mod_pattern(self, hypothesis: str):
        mod_pattern = r"p *≡ *([\d\sor]+)\(mod *(\d+)\)"
        match = re.search(mod_pattern, hypothesis)
        if not match:
            return "Could not parse modular condition for automated testing."

        residues_str = match.group(1).strip()
        mod_val = int(match.group(2))

        residues = [int(x.strip()) for x in residues_str.split('or') if x.strip().isdigit()]

        bound_match = re.search(r"p *>(\d+)", hypothesis)
        lower_bound = int(bound_match.group(1)) if bound_match else 2

        limit = 10000
        fail_count = 0
        counterexamples = []
        for n in range(lower_bound+1, limit):
            if isprime(n):
                if all((n % mod_val) != r for r in residues):
                    fail_count += 1
                    counterexamples.append(n)
                    if fail_count > 5:
                        break

        if fail_count == 0:
            return f"Empirical Verification Passed: No counterexamples found up to {limit}."
        else:
            return f"Empirical Verification Failed: Found {fail_count} counterexamples up to {limit}. First few: {counterexamples[:3]}"

    def test_hypothesis(self, hypothesis: str):
        if "collatz" in hypothesis.lower():
            return f"Empirical Testing of Modified Collatz Sequence:\n{self.test_collatz_sequence(hypothesis)}"
        elif "prime" in hypothesis.lower() and "mod" in hypothesis.lower():
            return self.test_prime_mod_pattern(hypothesis)
        return "No automated empirical verification was performed because hypothesis could not be parsed."

    def verify(self, pipeline_result: str):
        results = []
        
        # Extract and verify Lean proof
        lean_code = self.extract_lean_code(pipeline_result)
        if lean_code:
            lean_result = self.verify_lean_proof(lean_code)
            results.append(lean_result)
        else:
            results.append("No Lean code found in the pipeline result.")
        
        # Run empirical verification
        hypothesis = self.parse_hypothesis(pipeline_result)
        if hypothesis:
            empirical_result = self.test_hypothesis(hypothesis)
            results.append(empirical_result)
        else:
            results.append("No hypothesis found in the pipeline result.")
        
        return "\n\n".join(results)