"""
Compile optimized DSPy model using BootstrapFewShot
"""
import json
import os
import dspy
from dspy.teleprompt import BootstrapFewShot, MIPROv2
from dspy_extractors import BiologicalEntityExtractorModule, BiologicalEntityExtractor
from config import OPENROUTER_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DSPyCompiler:
    """Compile optimized DSPy module for production"""
    
    def __init__(self, annotations_file: str = "annotations_gold.json"):
        self.annotations_file = annotations_file
        teacher_lm = dspy.LM("gemini/gemini-flash-latest", api_key=os.environ.get("GEMINI_API_KEY"))

        
        # Strong LLM for few-shot selection
        # self.teacher_lm = dspy.LM(
        #     model="openrouter/deepseek/deepseek-chat-v3.1:free",
        #     api_base="https://openrouter.ai/api/v1",
        #     api_key=OPENROUTER_API_KEY
        # )
        self.teacher_lm = teacher_lm
        lm = dspy.LM(
    "openai/mistral-medium-latest",
    api_key=os.environ.get("MISTRAL_API_KEY"),
    api_base="https://api.mistral.ai/v1",
    max_tokens=2000000
)
        # Weak LLM for production
        # self.student_lm = dspy.LM(
        #     model="openrouter/deepseek/deepseek-r1:free",  # Much cheaper
        #     api_base="https://openrouter.ai/api/v1",
        #     api_key=OPENROUTER_API_KEY
        # )
        self.student_lm = lm
    
    def load_annotations(self):
        """Load gold-standard annotations"""
        with open(self.annotations_file, 'r') as f:
            annotations = json.load(f)
        
        logger.info(f" Loaded {len(annotations)} annotations")
        return annotations
    
    def prepare_training_examples(self, annotations):
        """Convert annotations to DSPy Example format"""
        examples = []
        
        for ann in annotations:
            input_data = ann['input']
            output_data = ann['output']
            
            # Create DSPy Example
            example = dspy.Example(
                title=input_data['title'],
                abstract=input_data['abstract'],
                keywords=input_data['keywords'],
                mesh_terms=input_data['mesh_terms'],
                # Expected outputs
                organisms=output_data['organisms'],
                phenomena=output_data['phenomena'],
                experimental_context=output_data['experimental_context'],
                platform=output_data['platform'],
                stressors=output_data['stressors']
            ).with_inputs('title', 'abstract', 'keywords', 'mesh_terms')
            
            examples.append(example)
        
        return examples
    
    def validation_metric(self, example, pred, trace=None):
        """
        Custom validation metric for entity extraction
        
        Returns:
            float: Score between 0.0 and 1.0
        """
        score = 0.0
        total_weight = 0.0
        
        # 1. Organisms accuracy (40% weight)
        if example.organisms and pred.organisms:
            org_names_gold = {o['name'].lower() for o in example.organisms}
            org_names_pred = {o['name'].lower() for o in pred.organisms}
            
            intersection = org_names_gold & org_names_pred
            union = org_names_gold | org_names_pred
            
            org_score = len(intersection) / len(union) if union else 0.0
            score += org_score * 0.4
        total_weight += 0.4
        
        # 2. Phenomena accuracy (40% weight)
        if example.phenomena and pred.phenomena:
            phen_names_gold = {p['name'].lower() for p in example.phenomena}
            phen_names_pred = {p['name'].lower() for p in pred.phenomena}
            
            intersection = phen_names_gold & phen_names_pred
            union = phen_names_gold | phen_names_pred
            
            phen_score = len(intersection) / len(union) if union else 0.0
            score += phen_score * 0.4
        total_weight += 0.4
        
        # 3. Context exact match (20% weight)
        if example.experimental_context == pred.experimental_context:
            score += 0.2
        total_weight += 0.2
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def compile_model(self, examples, method: str = "bootstrap"):
        """
        Compile optimized model
        
        Args:
            examples: Training examples
            method: 'bootstrap' or 'mipro'
        
        Returns:
            Compiled DSPy module
        """
        # Configure teacher (for few-shot selection)
        dspy.settings.configure(lm=self.teacher_lm)
        
        # Split train/val (80/20)
        split_idx = int(len(examples) * 0.8)
        train_examples = examples[:split_idx]
        val_examples = examples[split_idx:]
        
        logger.info(f" Training: {len(train_examples)}, Validation: {len(val_examples)}")
        
        # Initialize base module
        base_module = BiologicalEntityExtractorModule()
        
        if method == "bootstrap":
            # BootstrapFewShot: Fast, good results
            compiler = BootstrapFewShot(
                metric=self.validation_metric,
                max_bootstrapped_demos=4,  # Use 4 examples in prompt
                max_labeled_demos=4,
                teacher_settings=dict(lm=self.teacher_lm)
            )
            
            logger.info(" Compiling with BootstrapFewShot...")
            compiled_module = compiler.compile(
                student=base_module,
                trainset=train_examples
            )
            
        elif method == "mipro":
            # MIPROv2: Slower, better optimization
            # Option 1: Use auto mode (recommended for simplicity)
            compiler = MIPROv2(
                metric=self.validation_metric,
                auto="light"  # Options: "light", "medium", "heavy" (controls num_candidates/trials automatically)
            )
            
            logger.info(" Compiling with MIPROv2 auto='light' mode (this will take ~10-15 min)...")
            compiled_module = compiler.compile(
                student=base_module,
                trainset=train_examples,
                valset=val_examples
            )
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Evaluate on validation set
        logger.info(" Evaluating on validation set...")
        self._evaluate(compiled_module, val_examples)
        
        return compiled_module
    
    def _evaluate(self, module, examples):
        """Evaluate compiled module"""
        dspy.settings.configure(lm=self.student_lm)  # Use weak model for eval
        
        total_score = 0.0
        
        for example in examples:
            try:
                pred = module(
                    title=example.title,
                    abstract=example.abstract,
                    keywords=example.keywords,
                    mesh_terms=example.mesh_terms
                )
                
                score = self.validation_metric(example, pred)
                total_score += score
                
            except Exception as e:
                logger.error(f" Evaluation error: {e}")
        
        avg_score = total_score / len(examples)
        logger.info(f" Validation Accuracy: {avg_score:.2%}")
    
    def save_compiled_model(self, compiled_module, output_path: str = "compiled_extractor.json"):
        """Save compiled model"""
        compiled_module.save(output_path)
        logger.info(f" Saved compiled model to {output_path}")


def main():
    compiler = DSPyCompiler()
    
    # Load annotations
    annotations = compiler.load_annotations()
    examples = compiler.prepare_training_examples(annotations)
    
    # Compile with BootstrapFewShot (fast, ~2-3 min) or MIPROv2 (better, ~10-15 min)
    compiled = compiler.compile_model(examples, method="mipro")  # Change to "mipro" for better optimization
    
    # Save
    compiler.save_compiled_model(compiled)
    
    logger.info(" Compilation complete!")


if __name__ == "__main__":
    main()