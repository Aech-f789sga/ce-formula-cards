import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, "titles.json")
t = json.load(open(path, encoding="utf-8"))

overrides = {
"1":{"section":"Properties of Soil","titles":{"0":"Phase Diagram of Soil","1":"Degree of Saturation","2":"Moisture Content","3":"Void Ratio and Porosity","4":"Unit Weight","5":"Saturated Unit Weight","6":"Submerged Unit Weight (Buoyant)","7":"Bulk Specific Gravity (G)","8":"Moist Unit Weight Notes","9":"Specific Gravity of Solids (Gs)","10":"Special Notes on Soil"}},
"38":{"section":"Engineering Mechanics","titles":{"0":"Maximum Tension in Parabolic Cable","1":"Tensile Force in Catenary Cable","2":"Vertical Distance in Catenary","3":"Unsymmetrical Catenary Cable","4":"Symmetrical Catenary Cable","5":"Total Acceleration","6":"Tangential Acceleration"}},
"41":{"section":"Theory of Structures","titles":{"0":"Beams, Trusses & Frames Determinacy","1":"Number of Releases (S)","2":"Beam Stability Criteria","3":"Releases per Support Type","4":"Frames Determinacy (Loop Method)","5":"Truss Determinacy Criteria","6":"Moment Equation Sign Convention","7":"Impact Load Deflection","8":"Moment-Area Theorem 1","9":"Moment-Area Theorem 2","10":"Beam Deflection Diagrams","11":"Parabolic Spandrel Area & Centroid"}},
"51":{"section":"Steel Design","titles":{"0":"Average Web Shear Stress","1":"General Shear Stress","2":"Shear Flow","3":"Bolt Spacing","4":"Shearing Resistance","5":"Flexural Bending Stress","6":"Shear Stress (Other Sections)","7":"Bending Stress & Section Properties","8":"A36 Steel Yield Strength","9":"A36 Steel Ultimate Strength","10":"Modular Ratio","11":"Allowable Concrete Stress (Steel Design)"}},
"62":{"section":"Concrete Design","titles":{"0":"WSD Beam Analysis Diagrams","1":"Doubly Reinforced Uncracked Section","2":"Doubly Reinforced Cracked Section","3":"Flexural Stress (WSD)","4":"Allowable Concrete Stress","5":"Allowable Steel Stress"}},
"68":{"section":"Concrete Design","titles":{"0":"Simplified Vc (Shear & Flexure)","1":"Detailed Vc Calculation","2":"Shear with Axial Tension","3":"Simplified Vc with Axial Compression","4":"Mm for Axial Compression","5":"Detailed Vc with Axial Compression","6":"Circular Column Parameters","7":"Web Steel Ratio (ρw)"}},
"71":{"section":"Concrete Design","titles":{"0":"Tied Column Axial Load","1":"Tied Column Design Strength","2":"Reinforcement Ratio Limits (ρ)","3":"Minimum Tie Spacing","4":"Maximum Tie Spacing","5":"Spiral Column Axial Load","6":"Spiral Column Design Strength","7":"Minimum Bars per Column (Nmin)","8":"Volumetric Spiral Ratio (ρs)","9":"Maximum Spiral Spacing"}},
"108":{"section":"Surveying","titles":{"0":"Spiral Curve Formulas"}},
"109":{"section":"Surveying","titles":{"0":"Symmetrical Parabolic Vertical Curve","1":"Unsymmetrical Vertical Curve"}},
"135":{"section":"Refresher Notes","titles":{"0":"Stiffness Factor","1":"Limit of Economic Haul","2":"Survey Error Formulas","3":"Harmonic Motion & Energy","4":"Simple Pendulum Period","5":"Efficiency & Orbital Velocity"}},
}

t.update(overrides)
json.dump(t, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pages", len(t))
