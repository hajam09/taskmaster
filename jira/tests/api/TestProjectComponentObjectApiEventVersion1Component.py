import json

from django.core.cache import cache
from django.urls import reverse

from jira.models import Project, ProjectComponent
from taskmaster.operations import databaseOperations, bakerOperations
from taskmaster.tests import userDataHelper
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class ProjectComponentObjectApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('jira:projectComponentObjectApiEventVersion1Component')) -> None:
        self.testParams = self.TestParams().createProject()
        self.basePath = path
        super(ProjectComponentObjectApiEventVersion1ComponentTest, self).setUp(
            self.basePath + f'?project__id={self.testParams.project.id}'
        )

    def testGetAllProjectComponents(self):
        self.testParams.createProjectComponents(2)
        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertIsNotNone(ajaxResponse['data']['components'])
        self.assertEqual(2, len(ajaxResponse['data']['components']))

        for item in ajaxResponse['data']['components']:
            self.assertIsNotNone(item)
            self.assertIn('component', item['internalKey'])
            self.assertIn('description', item['description'])
            self.assertIsNotNone(item['status'])
            self.assertEqual(ProjectComponent.Status.ACTIVE, item['status']['internalKey'])
            self.assertIsNotNone(item['lead'])
            self.assertEqual(self.testParams.user.get_full_name(), item['lead']['fullName'])

    def testGetEmptyProjectComponents(self):
        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertIsNotNone(ajaxResponse['data']['components'])
        self.assertEqual(0, len(ajaxResponse['data']['components']))

    def testCreateNewProjectComponent(self):
        payload = {
            'internalKey': 'new component',
            'project_id': self.testParams.project.id,
            'lead_id': self.testParams.user.id,
            'description': 'sample description'
        }

        response = self.post(payload, self.basePath)
        ajaxResponse = json.loads(response.content)
        self.assertTrue(ajaxResponse["success"])
        self.assertTrue(ProjectComponent.objects.filter(**payload).exists())

    def testCreateExistingProjectComponent(self):
        self.testParams.createProjectComponents(1)
        component = self.testParams.ticketProjectComponents[0]
        payload = {
            'internalKey': component.internalKey,
            'project_id': component.project.id,
            'lead_id': component.lead.id,
            'description': component.description
        }
        response = self.post(payload, self.basePath)
        ajaxResponse = json.loads(response.content)
        self.assertFalse(ajaxResponse["success"])
        self.assertEquals(ajaxResponse["message"], "Component with this name already exists.")

    def testUpdateExistingProjectComponent(self):
        self.testParams.createProjectComponents(1)
        component = self.testParams.ticketProjectComponents[0]

        componentObject = ProjectComponent.objects.get(
            internalKey=component.internalKey,
            project_id=component.project.id,
            lead_id=component.lead.id
        )

        payload = {
            'filter': {
                'id': str(componentObject.id),
                'project_id': str(componentObject.project.id)
            },
            'update': {
                'internalKey': 'New Component Name',
                'description': 'New Description',
                'status': ProjectComponent.Status.ARCHIVED.name
            },
        }

        response = self.put(payload, self.basePath)
        ajaxResponse = json.loads(response.content)
        componentObject.refresh_from_db()

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(payload['update']['internalKey'], componentObject.internalKey)
        self.assertEqual(payload['update']['description'], componentObject.description)
        self.assertEqual(payload['update']['status'], componentObject.status)

    def testDeleteProjectComponent(self):
        self.testParams.createProjectComponents(1)
        component = self.testParams.ticketProjectComponents[0]

        componentObject = ProjectComponent.objects.get(
            internalKey=component.internalKey,
            project_id=component.project.id,
            lead_id=component.lead.id
        )

        payload = {
            'filter': {
                'id': str(componentObject.id),
                'project_id': str(componentObject.project.id)
            },
        }

        response = self.delete(payload, self.basePath)
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertFalse(ProjectComponent.objects.filter(**payload['filter']).exists())


    class TestParams:

        def __init__(self):
            self.project = None
            self.user = userDataHelper.createNewUser()
            bakerOperations.createProfileObjects([self.user])
            self.ticketProjectComponents = []

        def createProject(self):
            project = Project()
            project.internalKey = "Test Project"
            project.code = "TP"
            project.description = "Project description"
            project.lead = self.user
            project.status = databaseOperations.getObjectByCode(cache.get('PROJECT_STATUS'), "ON_GOING")
            project.save()
            self.project = project
            return self

        def createProjectComponents(self, counter):
            self.ticketProjectComponents = [
                ProjectComponent(
                    internalKey=f'component {i}',
                    project_id=self.project.id,
                    description=f'description {i}',
                    lead=self.user
                )
                for i in range(counter)
            ]

            ProjectComponent.objects.bulk_create(self.ticketProjectComponents)
            return self
