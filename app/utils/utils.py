from app import db
from flask import current_app
import csv
from app.models import User, Role, Owner
from datetime import datetime
from werkzeug.security import generate_password_hash

import os
    

import re

def replace_cite(content):
    return re.sub(r'\\cite\{(.*?)\}', r'[\1]', content)


def add_owner():
    if User.query.filter_by(role=Role.OWNER).first() is None:
        owner = Owner(
            name='admin',
            password_hash=generate_password_hash('admin'),
            role=Role.OWNER,
            first_login=True
        )
        db.session.add(owner)
        db.session.commit()
        print('Owner added to the database.')
    else:
        print('Owner already exists.')



from ..models import Knowledge, KnownItem, KnowledgeType, File, ProgressStatus, Theme, SharingStatus, Biblio

import os
import random
from datetime import datetime
from flask import current_app

def add_bibliographies():
    bibliographies = [
        {
            "name": "zweibel1982",
            "year": 1982,
            "title": "Magnetic reconnection in astrophysical and laboratory plasmas",
            "authors": "E. G. Zweibel and M. Yamada",
            "bibtex": "@article{zweibel1982, title={Magnetic reconnection in astrophysical and laboratory plasmas}, author={E. G. Zweibel and M. Yamada}, journal={Annual Review of Astronomy and Astrophysics}, volume={40}, number={1}, pages={141-171}, year={1982}, publisher={Annual Reviews}}"
        },
        {
            "name": "petschek1964",
            "year": 1964,
            "title": "Magnetic field annihilation",
            "authors": "H. E. Petschek",
            "bibtex": "@inproceedings{petschek1964, title={Magnetic field annihilation}, author={H. E. Petschek}, booktitle={The Physics of Solar Flares}, pages={425-439}, year={1964}, publisher={NASA Special Publication}}"
        },
        {
            "name": "priest2000",
            "year": 2000,
            "title": "Magnetic Reconnection: MHD Theory and Applications",
            "authors": "E. R. Priest and T. G. Forbes",
            "bibtex": "@book{priest2000, title={Magnetic Reconnection: MHD Theory and Applications}, author={E. R. Priest and T. G. Forbes}, year={2000}, publisher={Cambridge University Press}}"
        }
    ]

    for biblio_data in bibliographies:
        get_or_create(
            db.session,
            Biblio,
            name=biblio_data["name"],
            defaults={
                "year": biblio_data["year"],
                "title": biblio_data["title"],
                "authors": biblio_data["authors"],
                "bibtex": biblio_data["bibtex"],
                "file_id": None
            }
        )


def get_or_create(session, model, defaults=None, **kwargs):
    """
    Get an existing object or create a new one if it doesn't exist.
    :param session: SQLAlchemy session
    :param model: SQLAlchemy model
    :param defaults: Dictionary of additional attributes to set for new instances
    :param kwargs: Filtering criteria for querying
    :return: A tuple (instance, created), where created is True if a new instance was created
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = {**kwargs, **(defaults or {})}
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True



def init_db():
    # Create all tables
    db.create_all()

    add_bibliographies()

    knowledge_types = [
        {
            "name": "modelling",
            "description": (
                "The development and application of mathematical models or computational simulations to represent "
                "complex systems, enabling predictions about system behavior under different conditions."
            )
        },
        {
            "name": "measurements",
            "description": (
                "The use of experimental and observational techniques to accurately quantify and record properties and "
                "behaviors, providing essential data for validating hypotheses and refining models."
            )
        },
        {
            "name": "analytical solution",
            "description": (
                "The application of mathematical and logical techniques to derive exact solutions, shedding light on "
                "fundamental principles and boundary conditions in a given problem."
            )
        },
        {
            "name": "literature review",
            "description": (
                "Comprehensive review and synthesis of existing research to contextualize new findings, identify gaps, "
                "and inform future research directions."
            )
        },
        {
            "name": "data analysis",
            "description": (
                "The systematic examination and interpretation of data, uncovering patterns, trends, and insights to "
                "inform decisions and guide further research directions."
            )
        }
    ]
    for kt in knowledge_types:
        get_or_create(db.session, KnowledgeType, **kt)

    # Add Themes
    themes = [
        {
            "name": "High Energy Density Plasmas",
            "description": (
                "Research focusing on the behavior and dynamics of plasmas under extreme conditions, such as high pressure, "
                "temperature, and electromagnetic fields. This includes studying fusion, astrophysical plasmas, and "
                "laser-plasma interactions in controlled environments."
            ),
            "is_active": True
        },
        {
            "name": "Neutron and Proton Acceleration",
            "description": (
                "Exploring the acceleration mechanisms for neutrons and protons, especially in high-energy environments such "
                "as particle accelerators and astrophysical phenomena. This research involves understanding the interactions "
                "of charged particles with electromagnetic fields and their behavior in both laboratory and space settings."
            ),
            "is_active": True
        }
    ]
    for theme_data in themes:
        get_or_create(db.session, Theme, **theme_data)

    # Add Knowledge
    theme_high_energy_density, _ = get_or_create(
        db.session, Theme, name="High Energy Density Plasmas"
    )
    knowledge_entry, _ = get_or_create(
        db.session,
        Knowledge,
        name="mr in high-aspect ratio plasmas",
        defaults={
            "creator_name": "researcher",
            "theme_name": theme_high_energy_density.name,
            "description": "Study of magnetic reconnection in laser-produced high-aspect ratio plasmas",
            "sharing_status": SharingStatus.shared,
        }
    )

    zweibel1982 = db.session.query(Biblio).filter_by(name="zweibel1982").first()
    priest2000 = db.session.query(Biblio).filter_by(name="priest2000").first()

    # Define and Add Known Items
    items = [
        {
            "name": "snapshot",
            "description": (
                "Color-coded density, snapshot for the modeled configuration, black lines represent magnetic field lines."
            ),
            "content": (
                "We present the results of the 3D numerical simulations of the laser-produced plasmas magnetic "
                "reconnection in large-system size regime and consider collisionless ions cases including electron "
                "momentum transfer with/without additional allowance for the effects of electron-ion and ion-ion "
                "collisions. Such a model allows observing the formation and subsequent breakup of the reconnection "
                "current sheet. Following the experiments, we use pairs of laser-produced plumes from a flat target."
            ),
            "imgsrc": "fig1.png",
            "bibliography_ids":[],
            "typename": "modelling"
        },
        {
            "name": "bfield",
            "description": (
                "Collisonless case. Color-coded magnetic field $B_x$ with superposed isocontours of the magnetic potential "
                "at three times."
            ),
            "content": (
                "In this section, we discuss the collisionless case with only three terms on the RHS of Eq. (Ohm's law): ideal $V_i \\times B$, "
                "Hall  $J \\times B$, and pressure divergence term $\\sim \\nabla . P_e$. Figure 2(a) demonstrates the reconnecting magnetic field at $t\\Omega_0=10$, "
                "generated via noncollinear electron density and temperature gradients near the target surface and then advected by plasmas to "
                "the interaction region. The magnitude of the self-generated magnetic field by the Biermann battery effect in such a system is "
                "of the order of $0.1B_0$, consistent with previous numerical studies. At this time, the current sheet is highly-extended with length "
                "$80d_0$ and quasi-laminar with half-width $\\delta \\sim 1 d_0$. From Fig. 2(a), we find the upstream field at the edge of the current sheet is "
                "compressed by a factor of 1.5-2 the nominal generated field, aligning with fully kinetic three-dimensional modeling results."
            ),
            "imgsrc": "fig2.png",
            "bibliography_ids":[],
            "typename": "modelling"
        },
        {
            "name": "protonradiography",
            "description": (
                "Synthetic proton radiography, obtained by tracing proton-particles from a point-source through the "
                "simulation volume, and then projecting them ballistically to a detector plane. Color-coded number of "
                "protons per pixel. Proton source is positioned in different hemispheres to observe varied plasma "
                "interactions."
            ),
            "content": (
                "A sequence of proton radiographs shows the evolution of the plasma plumes, which includes formation "
                "and breakup of the current sheet. The dynamics resemble experimental observations, revealing the "
                "progression of transverse modulations, cellular morphologies, and wrapping structures."
            ),
            "imgsrc": "fig3.png",
            "bibliography_ids":[],
            "typename": "modelling"
        },
        {
            "name": "Ohm's law",
            "description": "Ohm's law for plasma systems with electric field and related terms.",
            "content": (
            "The equation governing the electric field in plasma, incorporating the effects of ideal terms, Hall "
            "terms, pressure divergence, and resistivity, is given as\\cite{zweibel1982,priest2000}: "
            "\\begin{equation} E = -V_i \\times B + \\frac{1}{en}(J \\times B - \\nabla . P_e) + \\eta J \\end{equation}"
            "Key parameters can be summarized in the following table:"
            "\\begin{array}{|c|c|c|}\n"
            "\\hline\n"
            "\\textbf{Term} & \\textbf{Expression} & \\textbf{Physical Meaning} \\\\ \\hline"
            "\\text{Ideal Term} & -V_i \\times B & \\text{Induction by plasma motion} \\\\ \\hline"
            "\\text{Hall Term} & \\frac{1}{en} J \\times B & \\text{Hall effect} \\\\ \\hline"
            "\\text{Pressure Divergence} & -\\frac{1}{en} \\nabla . P_e & \\text{Electron pressure gradient} \\\\ \\hline"
            "\\text{Resistive Term} & \\eta J & \\text{Ohmic heating} \\\\ \\hline"
            "\\end{array}"
        ),
            "imgsrc": None,
            "bibliography_ids":[zweibel1982.id, priest2000.id],
            "typename": "analytical solution"
        }
    ]
    for item_data in items:
        get_or_create(
            db.session,
            KnownItem,
            name=item_data["name"],
            defaults={
                "description": item_data["description"],
                "content": item_data["content"],
                "imgsrc": item_data["imgsrc"],
                "knowledge": knowledge_entry,
                "typename": item_data["typename"],
                "progress_status": ProgressStatus.inprogress,
                "bibliography_ids": item_data["bibliography_ids"]
            }
        )




