"""
RAGAS Evaluation Script for IndoGovRAG
Implements global RAG evaluation standards with Ollama

Requirements:
- ragas>=0.1.0
- sentence-transformers
- langchain-community
"""

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas import EvaluationDataset
import json
from pathlib import Path

# Configuration
OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GOLDEN_DATASET_PATH = "data/golden_dataset.json"
OUTPUT_PATH = "reports/ragas_evaluation.csv"

def setup_evaluators():
    """Setup Ollama LLM and embeddings for RAGAS"""
    # Use Ollama for LLM-as-judge
    ollama_llm = Ollama(model=OLLAMA_MODEL)
    evaluator_llm = LangchainLLMWrapper(ollama_llm)
    
    # Use local embeddings (same as semantic cache)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    evaluator_embeddings = LangchainEmbeddingsWrapper(embeddings)
    
    return evaluator_llm, evaluator_embeddings


def load_golden_dataset(path: str = GOLDEN_DATASET_PATH):
    """Load golden dataset for evaluation"""
    
    if not Path(path).exists():
        print(f"⚠️  Golden dataset not found at {path}")
        print("Creating sample dataset...")
        return create_sample_dataset()
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to RAGAS format
    ragas_data = []
    for item in data.get('queries', []):
        ragas_data.append({
            "user_input": item['user_input'],
            "retrieved_contexts": item['retrieved_contexts'],
            "response": item['response'],
            "reference": item.get('reference', '')  # Optional
        })
    
    return EvaluationDataset.from_list(ragas_data)


def create_sample_dataset():
    """Create sample dataset for testing"""
    sample_data = [
        {
            "user_input": "Apa syarat membuat KTP elektronik?",
            "retrieved_contexts": [
                "Pasal 63 UU No. 24 Tahun 2013: KTP Elektronik wajib dimiliki oleh WNI yang telah berumur 17 tahun atau sudah/pernah kawin.",
                "Syarat pembuatan KTP elektronik meliputi: Fotokopi Kartu Keluarga, Surat Keterangan Pindah (jika pindah domisili), dan mengisi formulir F-1.01."
            ],
            "response": "Syarat membuat KTP elektronik berdasarkan UU No. 24 Tahun 2013 adalah: 1) Berusia 17 tahun atau sudah/pernah menikah, 2) Membawa fotokopi Kartu Keluarga, 3) Mengisi formulir F-1.01, 4) Jika pindah domisili, membawa Surat Keterangan Pindah.",
            "reference": "Berdasarkan Pasal 63 UU 24/2013 dan prosedur Ditjen Dukcapil, syarat KTP elektronik adalah usia minimal 17 tahun atau sudah kawin, dengan dokumen Kartu Keluarga dan formulir F-1.01."
        },
        {
            "user_input": "Bagaimana cara mengurus akta kelahiran?",
            "retrieved_contexts": [
                "Pasal 32 UU No. 23 Tahun 2006: Pencatatan kelahiran dilakukan paling lambat 60 hari sejak kelahiran.",
                "Dokumen yang diperlukan: Surat keterangan kelahiran dari dokter/bidan, KTP dan KK orang tua, Buku Nikah orang tua."
            ],
            "response": "Cara mengurus akta kelahiran: 1) Datang ke kantor Dukcapil paling lambat 60 hari setelah kelahiran, 2) Bawa dokumen: Surat keterangan lahir dari dokter/bidan, KTP & KK orang tua, Buku Nikah, 3) Isi formulir permohonan, 4) Akta akan diterbitkan.",
            "reference": "Sesuai UU 23/2006 Pasal 32, akta kelahiran harus diurus maksimal 60 hari sejak lahir dengan membawa surat keterangan lahir, KTP/KK orang tua, dan Buku Nikah ke Dukcapil."
        }
    ]
    
    return EvaluationDataset.from_list(sample_data)


def run_evaluation():
    """Run RAGAS evaluation"""
    print("🔬 Starting RAGAS Evaluation for IndoGovRAG...")
    print(f"📊 Using model: {OLLAMA_MODEL}")
    print(f"📊 Using embeddings: {EMBEDDING_MODEL}\n")
    
    # Setup
    print("⚙️  Setting up evaluators...")
    evaluator_llm, evaluator_embeddings = setup_evaluators()
    
    # Load data
    print("📁 Loading golden dataset...")
    dataset = load_golden_dataset()
    print(f"✅ Loaded {len(dataset)} queries\n")
    
    # Run evaluation
    print("🚀 Running RAGAS evaluation (this may take a while)...\n")
    result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings
    )
    
    # Print results
    print("\n" + "="*60)
    print("📊 RAGAS EVALUATION RESULTS")
    print("="*60 + "\n")
    
    df = result.to_pandas()
    
    # Overall metrics
    print("Overall Metrics:")
    print(f"  Faithfulness:      {df['faithfulness'].mean():.3f} (target: >0.90)")
    print(f"  Answer Relevancy:  {df['answer_relevancy'].mean():.3f} (target: >0.80)")
    print(f"  Context Precision: {df['context_precision'].mean():.3f} (target: >0.70)")
    print(f"  Context Recall:    {df['context_recall'].mean():.3f} (target: >0.70)")
    
    # Grade
    overall_score = df[['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']].mean().mean()
    print(f"\n  Overall Score: {overall_score:.3f}")
    
    if overall_score >= 0.90:
        grade = "A+ (Excellent)"
    elif overall_score >= 0.85:
        grade = "A (Very Good)"
    elif overall_score >= 0.80:
        grade = "B+ (Good)"
    elif overall_score >= 0.75:
        grade = "B (Acceptable)"
    else:
        grade = "C (Needs Improvement)"
    
    print(f"  Grade: {grade}\n")
    
    # Per-query breakdown
    print("\nPer-Query Breakdown:")
    print("-" * 60)
    for idx, row in df.iterrows():
        print(f"\nQuery {idx + 1}:")
        print(f"  Faithfulness:      {row['faithfulness']:.3f}")
        print(f"  Answer Relevancy:  {row['answer_relevancy']:.3f}")
        print(f"  Context Precision: {row['context_precision']:.3f}")
        print(f"  Context Recall:    {row['context_recall']:.3f}")
    
    # Save results
    print(f"\n💾 Saving results to {OUTPUT_PATH}...")
    Path(OUTPUT_PATH).parent.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    
    print("✅ Evaluation complete!\n")
    
    return result


if __name__ == "__main__":
    try:
        result = run_evaluation()
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        print("\nMake sure you have installed:")
        print("  pip install ragas sentence-transformers langchain-community")
        raise
