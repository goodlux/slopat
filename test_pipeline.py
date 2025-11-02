#!/usr/bin/env python3
"""Test script for slop.at pipeline"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from slopat import process_file_simple
    
    def test_basic_processing():
        """Test the basic processing pipeline"""
        print("🚀 Testing slop.at pipeline...")
        
        # Test file
        test_file = project_root / "data" / "sample_conversation.txt"
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"📄 Processing: {test_file}")
        
        try:
            # Process the file
            result = process_file_simple(test_file, output_dir=project_root / "output")
            
            print(f"✅ Success! Generated: {result.slop_page.title}")
            print(f"📍 URL: {result.slop_page.url_path}")
            print(f"🧠 Concepts: {len(result.slop_page.concepts)}")
            print(f"💾 Saved to: {result.saved_path}")
            print(f"🗄️ Graph stored: {result.graph_stored}")
            
            # Show some extracted concepts
            print(f"\n🔍 Sample concepts:")
            for i, concept in enumerate(result.extraction_result.concepts[:5]):
                print(f"  {i+1}. {concept.text} ({concept.label}) - {concept.confidence:.2f}")
            
            print(f"\n📊 Domain distribution:")
            for domain, count in result.extraction_result.domain_distribution.items():
                print(f"  {domain}: {count}")
            
            return True
            
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("💡 Try: uv sync")
            return False
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        success = test_basic_processing()
        if success:
            print(f"\n🎉 slop.at pipeline test completed successfully!")
            print(f"🌐 Check the output directory for generated HTML")
        else:
            print(f"\n❌ Test failed")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Cannot import slop.at module: {e}")
    print("💡 Make sure all dependencies are installed: uv sync")
    sys.exit(1)
