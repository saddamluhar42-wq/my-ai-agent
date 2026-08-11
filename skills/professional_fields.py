from typing import Iterable, Tuple

from skills.registry import SkillDefinition


# Comprehensive professional skill catalog requested for the agent.
# Each entry becomes a routable skill so the planner can recognize
# specialized requests instead of treating everything as generic knowledge.
PROFESSIONAL_SKILLS: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    # Engineering, Manufacturing & Trades
    ("Engineering, Manufacturing & Trades", "mechanical_engineering", ("mechanical engineering", "mechanical engineer", "mechanics")),
    ("Engineering, Manufacturing & Trades", "electrical_wiring_circuit_design", ("electrical wiring", "circuit design", "electrical circuits")),
    ("Engineering, Manufacturing & Trades", "civil_drafting_surveying", ("civil drafting", "surveying", "land survey")),
    ("Engineering, Manufacturing & Trades", "cad_cam_design", ("cad", "cam", "cad/cam", "cad cam design")),
    ("Engineering, Manufacturing & Trades", "3d_modeling_printing", ("3d modeling", "3d printing", "3d model", "3d printer")),
    ("Engineering, Manufacturing & Trades", "cnc_machining", ("cnc machining", "cnc machine", "cnc")),
    ("Engineering, Manufacturing & Trades", "welding_fabrication", ("welding", "fabrication", "welder")),
    ("Engineering, Manufacturing & Trades", "carpentry_woodworking", ("carpentry", "woodworking", "carpenter")),
    ("Engineering, Manufacturing & Trades", "plumbing_pipefitting", ("plumbing", "pipefitting", "plumber")),
    ("Engineering, Manufacturing & Trades", "hvac_installation_maintenance", ("hvac", "air conditioning", "ac installation", "heating ventilation")),
    ("Engineering, Manufacturing & Trades", "industrial_automation", ("industrial automation", "factory automation", "plc automation")),
    ("Engineering, Manufacturing & Trades", "quality_control_six_sigma", ("quality control", "six sigma", "quality assurance")),
    ("Engineering, Manufacturing & Trades", "fleet_transport_management", ("fleet management", "transport management", "fleet")),
    ("Engineering, Manufacturing & Trades", "inventory_control", ("inventory control", "stock control", "inventory management")),
    ("Engineering, Manufacturing & Trades", "heavy_machinery_operation", ("heavy machinery", "heavy equipment", "machine operator")),

    # Healthcare, Medicine & Wellness
    ("Healthcare, Medicine & Wellness", "clinical_diagnostics", ("clinical diagnostics", "diagnostic testing", "diagnosis")),
    ("Healthcare, Medicine & Wellness", "nursing_patient_care", ("nursing", "patient care", "nurse")),
    ("Healthcare, Medicine & Wellness", "pharmacology", ("pharmacology", "pharmacology drugs", "drug science")),
    ("Healthcare, Medicine & Wellness", "physical_therapy_rehabilitation", ("physical therapy", "physiotherapy", "rehabilitation", "rehab")),
    ("Healthcare, Medicine & Wellness", "medical_billing_coding", ("medical billing", "medical coding", "medical coder")),
    ("Healthcare, Medicine & Wellness", "phlebotomy", ("phlebotomy", "blood draw", "phlebotomist")),
    ("Healthcare, Medicine & Wellness", "psychology_counseling", ("psychology", "counseling", "psychologist", "counselor")),
    ("Healthcare, Medicine & Wellness", "nutrition_dietetics", ("nutrition", "dietetics", "dietitian", "nutritionist")),
    ("Healthcare, Medicine & Wellness", "dental_assisting", ("dental assisting", "dental assistant", "dentistry assistant")),
    ("Healthcare, Medicine & Wellness", "radiology_medical_imaging", ("radiology", "medical imaging", "x ray", "mri", "ct scan")),
    ("Healthcare, Medicine & Wellness", "massage_therapy", ("massage therapy", "massage therapist")),
    ("Healthcare, Medicine & Wellness", "yoga_mindfulness_instructing", ("yoga", "mindfulness", "meditation instructor")),
    ("Healthcare, Medicine & Wellness", "public_health_administration", ("public health", "health administration", "public health administration")),
    ("Healthcare, Medicine & Wellness", "veterinary_care_animal_handling", ("veterinary care", "veterinary", "animal handling", "vet")),

    # Education, Training & Academia
    ("Education, Training & Academia", "curriculum_development", ("curriculum development", "curriculum design", "curriculum")),
    ("Education, Training & Academia", "elearning_course_design", ("e-learning", "elearning", "course design", "online course")),
    ("Education, Training & Academia", "classroom_management", ("classroom management", "classroom discipline", "classroom")),
    ("Education, Training & Academia", "special_education", ("special education", "special ed", "inclusive education")),
    ("Education, Training & Academia", "academic_tutoring", ("academic tutoring", "tutoring", "tutor")),
    ("Education, Training & Academia", "instructional_design", ("instructional design", "instructional designer")),
    ("Education, Training & Academia", "corporate_training_onboarding", ("corporate training", "employee onboarding", "onboarding training")),
    ("Education, Training & Academia", "educational_assessment", ("educational assessment", "student assessment", "assessment")),
    ("Education, Training & Academia", "research_methodology", ("research methodology", "research methods", "methodology")),
    ("Education, Training & Academia", "literature_review_academic_writing", ("literature review", "academic writing", "scholarly writing")),
    ("Education, Training & Academia", "student_career_counseling", ("career counseling", "student career", "career guidance")),

    # Legal, Compliance & Government
    ("Legal, Compliance & Government", "contract_drafting_review", ("contract drafting", "contract review", "contracts")),
    ("Legal, Compliance & Government", "intellectual_property_law", ("intellectual property", "ip law", "patent law", "copyright law", "trademark law")),
    ("Legal, Compliance & Government", "corporate_compliance", ("corporate compliance", "compliance", "regulatory compliance")),
    ("Legal, Compliance & Government", "legal_research", ("legal research", "case law research", "law research")),
    ("Legal, Compliance & Government", "paralegal_support", ("paralegal", "paralegal support", "legal assistant")),
    ("Legal, Compliance & Government", "dispute_resolution_arbitration", ("dispute resolution", "arbitration", "mediation")),
    ("Legal, Compliance & Government", "policy_analysis", ("policy analysis", "public policy", "policy research")),
    ("Legal, Compliance & Government", "risk_management", ("risk management", "risk assessment", "enterprise risk")),
    ("Legal, Compliance & Government", "fraud_investigation", ("fraud investigation", "fraud detection", "forensic fraud")),
    ("Legal, Compliance & Government", "notary_public_services", ("notary", "notary public", "notarization")),

    # Fine Arts, Music & Entertainment
    ("Fine Arts, Music & Entertainment", "illustration_digital_drawing", ("illustration", "digital drawing", "digital art")),
    ("Fine Arts, Music & Entertainment", "fine_art_painting", ("fine art painting", "painting", "fine art")),
    ("Fine Arts, Music & Entertainment", "sculpting_clay_work", ("sculpting", "sculpture", "clay work", "clay art")),
    ("Fine Arts, Music & Entertainment", "music_theory", ("music theory", "harmony", "music notation")),
    ("Fine Arts, Music & Entertainment", "vocal_performance_singing", ("singing", "vocal performance", "vocalist", "voice training")),
    ("Fine Arts, Music & Entertainment", "instrument_playing", ("instrument playing", "musical instrument", "guitar", "piano", "drums")),
    ("Fine Arts, Music & Entertainment", "music_composition", ("music composition", "song composition", "composer")),
    ("Fine Arts, Music & Entertainment", "audio_mastering", ("audio mastering", "mastering", "audio engineer")),
    ("Fine Arts, Music & Entertainment", "acting_drama", ("acting", "drama", "actor", "theatre")),
    ("Fine Arts, Music & Entertainment", "dance_choreography", ("dance", "choreography", "choreographer")),
    ("Fine Arts, Music & Entertainment", "event_hosting_mcing", ("event hosting", "mc", "emcee", "event host")),
    ("Fine Arts, Music & Entertainment", "makeup_artistry", ("make-up artistry", "makeup artistry", "makeup artist")),
    ("Fine Arts, Music & Entertainment", "costume_fashion_design", ("costume design", "fashion design", "fashion designer")),
    ("Fine Arts, Music & Entertainment", "stage_set_design", ("stage design", "set design", "stage set")),

    # Agriculture, Environment & Science
    ("Agriculture, Environment & Science", "agronomy_farming", ("agronomy", "farming", "agriculture", "farmer")),
    ("Agriculture, Environment & Science", "horticulture_landscaping", ("horticulture", "landscaping", "gardening", "landscape design")),
    ("Agriculture, Environment & Science", "pest_disease_control", ("pest control", "crop disease", "plant disease", "pest management")),
    ("Agriculture, Environment & Science", "animal_husbandry", ("animal husbandry", "livestock", "animal farming")),
    ("Agriculture, Environment & Science", "environmental_conservation", ("environmental conservation", "conservation", "environment protection")),
    ("Agriculture, Environment & Science", "geographic_information_systems", ("gis", "geographic information systems", "geospatial")),
    ("Agriculture, Environment & Science", "climate_weather_analysis", ("climate analysis", "weather analysis", "climate science", "meteorology")),
    ("Agriculture, Environment & Science", "laboratory_techniques", ("laboratory techniques", "lab techniques", "laboratory")),
    ("Agriculture, Environment & Science", "chemical_analysis", ("chemical analysis", "chemistry analysis", "analytical chemistry")),
    ("Agriculture, Environment & Science", "biotechnology", ("biotechnology", "biotech")),
    ("Agriculture, Environment & Science", "statistical_modeling", ("statistical modeling", "statistical modelling", "statistics model")),
    ("Agriculture, Environment & Science", "botany_plant_science", ("botany", "plant science", "botanical science")),

    # Real Estate, Architecture & Hospitality
    ("Real Estate, Architecture & Hospitality", "architectural_design", ("architectural design", "architecture", "architect")),
    ("Real Estate, Architecture & Hospitality", "urban_city_planning", ("urban planning", "city planning", "urban design")),
    ("Real Estate, Architecture & Hospitality", "real_estate_valuation_appraisal", ("real estate valuation", "property appraisal", "real estate appraisal", "property valuation")),
    ("Real Estate, Architecture & Hospitality", "property_management", ("property management", "property manager", "rental management")),
    ("Real Estate, Architecture & Hospitality", "facility_management", ("facility management", "facilities management", "facility manager")),
    ("Real Estate, Architecture & Hospitality", "hotel_management", ("hotel management", "hotel operations", "hotel manager")),
    ("Real Estate, Architecture & Hospitality", "tourism_travel_management", ("tourism management", "travel management", "tourism", "travel management")),
    ("Real Estate, Architecture & Hospitality", "tour_guiding", ("tour guide", "tour guiding", "tourist guide")),
    ("Real Estate, Architecture & Hospitality", "mixology_bartending", ("mixology", "bartending", "bartender")),
    ("Real Estate, Architecture & Hospitality", "food_safety_sanitation", ("food safety", "food sanitation", "sanitation")),
    ("Real Estate, Architecture & Hospitality", "concierge_guest_services", ("concierge", "guest services", "guest relations")),

    # Gaming & Deep Tech
    ("Gaming & Deep Tech", "game_mechanics_design", ("game mechanics", "game design", "game systems")),
    ("Gaming & Deep Tech", "3d_animation_rigging", ("3d animation", "rigging", "character rigging", "3d animator")),
    ("Gaming & Deep Tech", "level_design_environment_building", ("level design", "environment building", "game level")),
    ("Gaming & Deep Tech", "vr_ar_development", ("vr", "ar", "virtual reality", "augmented reality", "vr/ar development")),
    ("Gaming & Deep Tech", "cryptography_encryption", ("cryptography", "encryption", "cryptographic")),
    ("Gaming & Deep Tech", "blockchain_smart_contract_development", ("blockchain", "smart contract", "smart contracts", "web3")),
    ("Gaming & Deep Tech", "ethical_hacking_penetration_testing", ("ethical hacking", "penetration testing", "pentesting", "security testing")),
    ("Gaming & Deep Tech", "machine_learning_algorithms", ("machine learning", "ml algorithms", "machine learning algorithms", "ml")),
    ("Gaming & Deep Tech", "quantum_computing_basics", ("quantum computing", "quantum computer", "quantum algorithms")),
)


def register_professional_skills(registry) -> None:
    for category, name, keywords in PROFESSIONAL_SKILLS:
        registry.register(
            SkillDefinition(
                name=name,
                description=(
                    f"Professional skill: {name.replace('_', ' ')}. "
                    f"Category: {category}. Provide explanations, "
                    "planning, analysis, learning support and practical guidance "
                    "within this domain."
                ),
                keywords=list(keywords) + [name.replace("_", " ")],
                priority=78,
                enabled=True,
            )
        )
