from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import date

from django.test.testcases import TestCase
from mock import patch

from corehq.apps.userreports.models import StaticDataSourceConfiguration
from corehq.apps.userreports.util import get_indicator_adapter
from custom.aaa.dbaccessors import PregnantWomanQueryHelper
from custom.aaa.models import CcsRecord, Woman


class TestPregnantWomanBeneficiarySections(TestCase):
    domain = 'reach-test'

    @classmethod
    def setUpClass(cls):
        super(TestPregnantWomanBeneficiarySections, cls).setUpClass()
        Woman.objects.create(
            domain=cls.domain,
            person_case_id='person_case_id',
            opened_on='2019-01-01',
            blood_group='b_pos',
        )
        CcsRecord.objects.create(
            domain=cls.domain,
            person_case_id='person_case_id',
            ccs_record_case_id='ccs_record_case_id',
            opened_on='2019-01-01',
            hrp='yes',
            lmp='2018-12-03',
            woman_weight_at_preg_reg=54,
            preg_reg_date='2018-12-31',
            edd='2019-07-27',
            add='2019-07-31',
        )
        cls.adapters = []
        add_preg_adapter = cls._init_table('reach-add_pregnancy')
        add_preg_adapter.save({
            '_id': 'bp_form',
            'domain': cls.domain,
            'doc_type': "XFormInstance",
            'xmlns': 'http://openrosa.org/formdesigner/362f76b242d0cfdcec66776f9586dc3620e9cce5',
            'form': {
                "case_open_ccs_record_1": {"case": {"@case_id": 'ccs_record_case_id'}},
                "pregnancy": {"past_illness": "malaria", "past_illness_details": "took_malarone"},
                "meta": {"timeEnd": "2019-01-01T10:37:00Z"},
            },
        })
        bp_adapter = cls._init_table('reach-birth_preparedness')
        bp_adapter.save({
            '_id': 'bp_form',
            'domain': cls.domain,
            'doc_type': "XFormInstance",
            'xmlns': 'http://openrosa.org/formdesigner/2864010F-B1B1-4711-8C59-D5B2B81D65DB',
            'form': {
                "case_load_ccs_record0": {"case": {"@case_id": 'ccs_record_case_id'}},
                "date_referral": "2018-12-07",
                "place_referral": "chc",
                "bp2": {"inform_danger_signs": 'yes'},
                "meta": {"timeEnd": "2019-01-01T10:37:00Z"},
            },
        })
        thr_adapter = cls._init_table('reach-thr_forms')
        thr_adapter.save({
            '_id': 'thr_form',
            'domain': cls.domain,
            'doc_type': "XFormInstance",
            'xmlns': 'http://openrosa.org/formdesigner/F1B73934-8B70-4CEE-B462-3E4C81F80E4A',
            'form': {
                "case_load_ccs_record_0": {"case": {"@case_id": 'ccs_record_case_id'}},
                "thr_amount_1": 30,
                "thr_amount_2": 45,
                "meta": {"timeEnd": "2019-01-01T10:37:00Z"},
            },
        })
        delivery_adapter = cls._init_table('reach-delivery_forms')
        delivery_adapter.save({
            '_id': 'del_form',
            'domain': cls.domain,
            'doc_type': "XFormInstance",
            'xmlns': 'http://openrosa.org/formdesigner/376FA2E1-6FD1-4C9E-ACB4-E046038CD5E2',
            'form': {
                "case_load_ccs_record0": {"case": {"@case_id": 'ccs_record_case_id'}},
                "meta": {"timeEnd": "2019-01-01T10:37:00Z"},
                'where_born': 'hospital',
            },
        })
        person_adapter = cls._init_table('reach-person_cases')
        person_adapter.save({
            '_id': 'person_case_id',
            'domain': cls.domain,
            'doc_type': "CommCareCase",
            'type': 'person',
        })
        ccs_adapter = cls._init_table('reach-ccs_record_cases')
        ccs_adapter.save({
            '_id': 'ccs_record_case_id',
            'domain': cls.domain,
            'doc_type': "CommCareCase",
            'type': 'ccs_record',
            'ifa_tablets_issued_pre': 48,
            'ifa_tablets_issued_post': 2,
        })

        tasks_adapter = cls._init_table('reach-tasks_cases')
        immun_dates = {'tt_1': 32, 'tt_2': 85}
        with patch('corehq.apps.userreports.indicators.get_values_by_product', return_value=immun_dates):
            tasks_adapter.save({
                '_id': 'tasks_case',
                'domain': cls.domain,
                'doc_type': "CommCareCase",
                'type': 'tasks',
                "indices": [
                    {
                        "case_id": "tasks_case",
                        "identifier": "parent",
                        "referenced_id": "ccs_record_case_id",
                        "referenced_type": "ccs_record",
                        "relationship": "extension"
                    }
                ],
            })

    @classmethod
    def tearDownClass(cls):
        for adapter in cls.adapters:
            adapter.drop_table()
        CcsRecord.objects.all().delete()
        Woman.objects.all().delete()
        super(TestPregnantWomanBeneficiarySections, cls).tearDownClass()

    @classmethod
    def _init_table(cls, data_source_id):
        datasource_id = StaticDataSourceConfiguration.get_doc_id(cls.domain, data_source_id)
        datasource = StaticDataSourceConfiguration.by_id(datasource_id)
        adapter = get_indicator_adapter(datasource)
        adapter.build_table()
        cls.adapters.append(adapter)
        return adapter

    @property
    def _helper(self):
        return PregnantWomanQueryHelper(self.domain, 'person_case_id', date(2019, 2, 1))

    def test_pregnancy_details(self):
        self.assertEqual(
            self._helper.pregnancy_details(),
            {
                'lmp': date(2018, 12, 03),
                'weightOfPw': 54,
                'dateOfRegistration': date(2018, 12, 31),
                'edd': date(2019, 7, 27),
                'add': date(2019, 7, 31),
                'bloodGroup': 'b_pos',
            })

    def test_pregnancy_risk(self):
        self.assertEqual(
            self._helper.pregnancy_risk(),
            {
                'riskPregnancy': 'yes',
                'referralDate': date(2018, 12, 7),
                'referredOutFacilityType': 'chc',
                'hrpSymptoms': 'N/A',
                'illnessHistory': 'malaria',
                'pastIllnessDetails': 'took_malarone',
            })

    def test_consumables_disbursed(self):
        self.assertEqual(
            self._helper.consumables_disbursed(),
            {
                'ifaTablets': 50,
                'thrDisbursed': 75,
            })

    def test_immunization_counseling_details(self):
        self.assertEqual(
            self._helper.immunization_counseling_details(),
            {
                'ttDoseOne': date(1970, 2, 2),
                'ttDoseTwo': date(1970, 3, 27),
                'ttBooster': 'N/A',
                'birthPreparednessVisitsByAsha': 0,
                'birthPreparednessVisitsByAww': 0,
                'counsellingOnMaternal': True,
                'counsellingOnEbf': False,
            })

    def test_abortion_details(self):
        self.assertEqual(
            self._helper.abortion_details(),
            {
                'abortionDate': 'N/A',
                'abortionType': 'N/A',
                'abortionDays': 'N/A',
            })

    def test_maternal_death_details(self):
        self.assertEqual(
            self._helper.maternal_death_details(),
            {
                'maternalDeathOccurred': False,
                'maternalDeathPlace': 'N/A',
                'maternalDeathDate': 'N/A',
                'authoritiesInformed': 'N/A',
            })

    def test_delivery_details(self):
        self.assertEqual(
            self._helper.delivery_details(),
            {
                'dod': date(2019, 7, 31),
                'assistanceOfDelivery': 'N/A',
                'timeOfDelivery': 'N/A',
                'dateOfDischarge': 'N/A',
                'typeOfDelivery': 'N/A',
                'timeOfDischarge': 'N/A',
                'placeOfBirth': 'hospital',
                'deliveryComplications': 'N/A',
                'placeOfDelivery': 'N/A',
                'complicationDetails': 'N/A',
                'hospitalType': 'N/A',
            })

    def test_postnatal_care_details(self):
        self.assertEqual(
            self._helper.postnatal_care_details(),
            [{
                'pncDate': '2019-08-20',
                'postpartumHeamorrhage': 0,
                'fever': 1,
                'convulsions': 0,
                'abdominalPain': 0,
                'painfulUrination': 0,
                'congestedBreasts': 1,
                'painfulNipples': 0,
                'otherBreastsIssues': 0,
                'managingBreastProblems': 0,
                'increasingFoodIntake': 1,
                'possibleMaternalComplications': 1,
                'beneficiaryStartedEating': 0,
            }])

    def test_antenatal_care_details(self):
        self.assertEqual(
            self._helper.antenatal_care_details(),
            [{
                'ancDate': 'N/A',
                'ancLocation': 'N/A',
                'pwWeight': 'N/A',
                'bloodPressure': 'N/A',
                'hb': 'N/A',
                'abdominalExamination': 'N/A',
                'abnormalitiesDetected': 'N/A',
            }])
