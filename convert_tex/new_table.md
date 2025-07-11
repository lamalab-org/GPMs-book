::: {#tab:molecular-representations}
  **Representation**                                                   **Encoded information**                                                    **Description**                                                                                                                                                                                                                                               **Example**
  -------------------------------------------------------------------  -------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Elemental composition                                                Stoichiometry                                                              Always available, but non-unique.                                                                                                                                                                                                                             C9H8O4
  \acr{iupac} name                                                     Stoichiometry, bonding, geometry                                           Universally understood, systematic nomenclature, unmanageable for large molecules, and lacks detailed 3D information.                                                                                                                                         2-acetyloxybenzoic acid
  \acr{smiles} \[@weininger1988smiles\]                                Stoichiometry, bonding                                                     Massive public corpora and tooling support, however, there are several valid strings per molecule, and it does not contain spatial information.                                                                                                               `CC(=O)OC1=CC=CC=C1C(=O)O`, `O=C(O)c1ccccc1OC(C)=O`, *etc.*
  \acr{selfies} \[@krenn2020self\]; \[@cheng2023group\]                Stoichiometry, bonding                                                     100% syntactic and semantic validity by construction, including meaningful grouping.                                                                                                                                                                          `[C][C][=Branch1][C][=O][O][C][=C][C][=C][C][=C][Ring1][=Branch1][C][=Branch1][C][=O][O]`
  \acr{inchi}                                                          Stoichiometry, bonding                                                     Canonical one-to-one identifier; encodes stereochemistry layers.                                                                                                                                                                                              `InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)`
  Graphs                                                               Stoichiometry, bonding, geometry                                           Strong inductive bias that works with gnns. Symmetry-equivariant variants available. Long-range interactions are implicit.                                                                                                                                    ![](media/figures/Aspirin.png)
  xyz representation                                                   Stoichiometry, geometry                                                    Exact spatial detail. It is high dimensional, and orientation alignment is needed.                                                                                                                                                                            1.2333 0.5540 0.7792 O -0.6952 -2.7148 -0.7502 O 0.7958 -2.1843 0.8685 O 1.7813 0.8105 -1.4821 O -0.0857 0.6088 0.4403 C ...
  Multimodal                                                           Stoichiometry, bonding, geometry, symmetry, periodicity, coarse graining   Combines complementary signals; boosts robustness and coverage. It is hard to implement, the complexity scales with the amount of representations, some modalities are data-scarce, and the information encoded totally depends on the modalities included.   ![](media/figures/60031761.jpeg)
  \acr{cif} \[@hall1991crystallographic\]                              Stoichiometry, bonding, geometry, periodicity                              Standardized and widely supported, however, it carries heterogeneous keyword sets and parser overhead                                                                                                                                                         `data_Si _symmetry_space_group_name_H-M ’P 1’ _cell_length_a 3.85 …_cell_angle_alpha 60.0 …_symmetry_Int_Tables_number 1 _chemical_formula_structural Si _chemical_formula_sum Si2 _cell_volume 40.33 _cell_formula_units_Z 2 loop_ _symmetry_equiv_pos_site_id _symmetry_equiv_pos_as_xyz 1 ’x, y, z’ loop_ _atom_type_symbol _atom_type_oxidation_number Si0+ 0.0loop_ _atom_site_type_symbol _atom_site_label _atom_site_symmetry_multiplicity _atom_site_fract_x …_atom_site_occupancy Si0+ Si0 1 0.75 0.75 0.75 1.0 Si0+ Si1 1 0.0 0.0 0.0 1.0`
  Condensed \acr{cif} \[@gruver2024finetuned; @antunes2024crystal\]    Stoichiometry, geometry, symmetry, periodicity                             Good for crystal generation tasks. It omits occupancies and defects, custom tooling is needed, and only works for crystals                                                                                                                                    `3.8 3.8 3.8 59 59 59 Si0+ 0.75 0.75 0.75 Si0+ 0.00 0.00 0.00`
  \acr{slices} \[@Xiao_2023\]                                          Stoichiometry, bonding, periodicity                                        Invertible, symmetry-invariant and compact for general crystals. However, it carries ambiguity for disordered sites                                                                                                                                           `Si Si 0 1 + + + 0 1 + + o 0 1 + o + 0 1 o + +`
  \acr{localenv} \[@alampara2024mattext\]                              Stoichiometry, bonding, symmetry, coarse graining                          Treats each coordination polyhedron as a "molecule", it is transferable and compact; but it ignores long-range order and its reconstruction requires post-processing                                                                                          `R-3m Si (2c) [Si][Si]([Si])[Si]`
  Natural-language description \[@ganose2019robocrystallographer\]     Stoichiometry, bonding, geometry, symmetry, periodicity, coarse graining   It is human-readable and more intuitive tokenizable by llms. However, trying to encode all the information can lead to verbose, ambiguous descriptions.                                                                                                       "Silicon crystallizes in the diamond-cubic structure, a lattice you can picture as two face-centred-cubic frameworks gently interpenetrating..."

  : **Comparison of common molecular representations**. For the encoded
  information contained by each representation, we followed the criteria
  used by \[@alampara2024mattext\]. The examples shown are *aspirin* for
  elemental composition, \acr{iupac} name, \acr{smiles}, \acr{selfies}, , graphs, 3D coordinates; and
  *silicon* for , condensed , , , and natural-language description. Two
  non-canonical \acr{smiles} are shown to illustrate ambiguity. The
  examples for 3D coordinates, , and natural-language description are
  truncated to fit in the table. For the multimodal representation, only
  one of the possible modalities is shown ($^{13}$C spectrum).
:::

::: {#tab:property_prediction_models}


| Model | Property | Dataset | Approach | Task |
|-------|----------|---------|----------|------|
| **GPT-Chem** [@jablonka2024leveraging] | HOMO/LUMO | QMUGs [@isert_qmugs_2022] | FT | C, R |
| | Solubility | DLS-100 [@mitchell_dls-100_2017] | FT | C, R |
| | Lipophilicity | LipoData [@jablonka2024leveraging] | FT | C, R |
| | Hydration Free Energy | FreeSolv [@mobley_freesolv_2014] | FT | C, R |
| | Photoconversion Efficiency | OPV [@jablonka2024leveraging] | FT | C, R |
| | Toxicology | Tox21 [@richard_tox21_2021] | FT | C, R |
| | $\text{CO}_{2}$ Henry coeff. of MOFs | MOFSorb-H [@lin_silico_2012] | FT | C, R |
| **LLM-Prop** [@rubungo_llm-prop_2023] | Band gap | CrystalFeatures-MP2022 [@rubungo_llm-prop_2023] | P | R |
| | Volume | CrystalFeatures-MP2022 [@rubungo_llm-prop_2023] | P | R |
| | Is the band gap direct? | CrystalFeatures-MP2022 [@rubungo_llm-prop_2023] | P | C |
| **LLM4SD** [@zheng2025large] | Blood-brain-barrier penetration | BBBP [@sakiyama_prediction_2021] | P | C |
| | FDA approval | ClinTox [@wu2018moleculenet] | P | C |
| | Toxicology | Tox21 [@richard_tox21_2021] | P | C |
| | Drug-related side effects | SIDER [@kuhn_sider_2016] | P | C |
| | HIV replication inhibition | HIV [@wu2018moleculenet] | P | C |
| | β-secretase binding | BACE [@wu2018moleculenet] | P | C |
| | Solubility | ESOL [@wu2018moleculenet] | P | R |
| | Hydration Free Energy | FreeSolv [@mobley_freesolv_2014] | P | R |
| | Lipophilicity | Lipophilicity [@wu2018moleculenet] | P | R |
| | Quantum mechanics | QM9 [@wu2018moleculenet] | P | R |
| **LLaMP** [@chiang2024llamp] | Bulk modulus | Materials Project [@riebesell2025framework] | RAG | R |
| | Formation energy | Materials Project [@riebesell2025framework] | RAG | R |
| | Electronic band gap | Materials Project [@riebesell2025framework] | RAG | R |
| | Multi-element band gap | Materials Project [@riebesell2025framework] | RAG | R |

  : **Non-comprehensive list of \arc{gmp}s applied to property-prediction tasks**.The table presents different models and their applications across different molecular and materials property prediction benchmarks, showing the diversity of properties (from molecular toxicology to crystal band gaps), datasets used for evaluation, modeling approaches (prompting, fine-tuning, or retrieval-augmented generation), and task types (classification or regression.)
:::

::: tablenotes
*Key:* P = prompting; FT = fine-tuned model; RAG = retrieval-augmented generation; C = classification; R = regression
:::

::: {#tab:small_large_datasets}
+----------------------------------------------------+-------------------+
| **Dataset**                                        | **Token count**   |
+:===================================================+==================:+
| *Three largest ChemPile datasets*                                      |
+----------------------------------------------------+-------------------+
| NOMAD crystal structures\[@scheidgen2023nomad\]    | 5,808,052,794     |
+----------------------------------------------------+-------------------+
| \acr{ord}\[@Kearnes_2021\] reaction prediction     | 5,347,195,320     |
+----------------------------------------------------+-------------------+
| `RDKit` molecular features                         | 5,000,435,822     |
+----------------------------------------------------+-------------------+
| *Three smallest ChemPile datasets*                                     |
+----------------------------------------------------+-------------------+
| Hydrogen storage                                   | 1,935             |
| materials\[@hymarcReversibleHydrides\]             |                   |
+----------------------------------------------------+-------------------+
| List of amino-acids\[@alberts2002molecular\]       | 6,000             |
+----------------------------------------------------+-------------------+
| \acr{ord}\[@Kearnes_2021\] recipe yield prediction | 8,372             |
+----------------------------------------------------+-------------------+

: **Token counts for the three largest and smallest datasets in the
`ChemPile`\[@mirza2025chempile0\] collection.** Dominating datasets
contribute a large portion of the total token count (a token represents
the smallest unit of text that a \acr{ml} model can process), with the small
datasets significantly increasing the diversity.
:::