#!/usr/bin/env python3
"""
Test script to verify the REAL langextract API works correctly
Based on the sample code from README.md
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_langextract_api():
    """Test the real langextract API using the sample from README"""
    try:
        import langextract as lx

        print("📋 Testing REAL langextract API from README sample...")

        # Check for API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ No GEMINI_API_KEY found in environment")
            print("💡 Add your Gemini API key to .env file to test real langextract")
            return False

        print(f"✅ API key found: {api_key[:8]}...")

        legal_text = """
        This Lease Agreement is entered into on September 21, 2025. The lease begins on
        October 1, 2025 and rent is due on the 5th of every month.
        """.strip()

        examples = [
            lx.data.ExampleData(
                text="This contract was signed on March 15, 2024 and becomes effective on April 1, 2024.",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="contract_date",
                        extraction_text="March 15, 2024",
                        attributes={"normalized_date": "2024-03-15", "type": "signing_date"},
                    ),
                    lx.data.Extraction(
                        extraction_class="effective_date",
                        extraction_text="April 1, 2024",
                        attributes={"normalized_date": "2024-04-01", "type": "effective_date"},
                    ),
                ],
            )
        ]

        print("🚀 Making real langextract API call...")

        response = lx.extract(
            text_or_documents=legal_text,
            prompt_description="Extract every legally meaningful date and provide a normalized ISO date.",
            examples=examples,
            model_id="gemini-2.0-flash-exp",
            api_key=api_key,
        )

        print(f"✅ SUCCESS! Found {len(response.extractions)} extractions:")

        for item in response.extractions:
            attrs = item.attributes or {}
            print(f"  📅 {item.extraction_class} → {item.extraction_text} → {attrs.get('normalized_date', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ langextract API test failed: {e}")
        return False

def test_our_implementation():
    """Test our langextract implementation"""
    try:
        from src.extractors.langextract_date_extractor import LangextractDateExtractor

        print("\n📋 Testing our langextract implementation...")

        extractor = LangextractDateExtractor()
        print(f"🔍 Available: {extractor.is_available()}")

        if not extractor.is_available():
            print("❌ Our implementation not available - missing API key")
            return False

        test_text = "This Agreement is entered into on March 15, 2024, and becomes effective on April 1, 2024."

        print("🚀 Testing our extraction method...")
        result = extractor.extract_structured_dates(test_text)

        print(f"✅ Our implementation result:")
        print(f"  Success: {result['langextract_success']}")
        print(f"  Method: {result['extraction_method']}")
        print(f"  Dates found: {len(result['all_dates'])}")
        for date in result['all_dates']:
            print(f"    📅 {date}")

        return result['langextract_success']

    except Exception as e:
        print(f"❌ Our implementation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing langextract API compatibility\n")

    # Test the raw API first
    api_works = test_langextract_api()

    # Test our implementation
    our_impl_works = test_our_implementation()

    print(f"\n📊 Results:")
    print(f"  Raw langextract API: {'✅ WORKS' if api_works else '❌ FAILED'}")
    print(f"  Our implementation: {'✅ WORKS' if our_impl_works else '❌ FAILED'}")

    if api_works and our_impl_works:
        print("\n🎯 SUCCESS! Ready for TRUE docling + langextract testing!")
    elif not api_works:
        print("\n⚠️  Add GEMINI_API_KEY to .env to test real langextract")
    else:
        print("\n❌ Implementation needs fixing")