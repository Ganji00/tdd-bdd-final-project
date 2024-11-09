# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_deserialize_invalid_attribute(self):
        """It should raise DataValidationError for invalid attribute"""
        product_data = {
            "name": "TestProduct",
            "description": "Invalid attribute example",
            "price": "10.00",
            "available": True,
            "category": "INVALID_CATEGORY"  # invalid category
        }
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(product_data)
        self.assertIn("Invalid attribute:", str(context.exception))

    def test_update_product(self):
        """It should Update an existing product's attributes"""
        product = ProductFactory()
        product.create()
        product.description = "Updated description"
        product.update()
        # Retrieve to check if updates persist
        updated_product = Product.find(product.id)
        self.assertEqual(updated_product.description, "Updated description")

    def test_delete_product(self):
        """It should Delete a product from the database"""
        product = ProductFactory()
        product.create()
        self.assertIsNotNone(Product.find(product.id))
        product.delete()
        self.assertIsNone(Product.find(product.id))

    def test_find_by_name(self):
        """It should find products by name"""
        product_name = "SpecialProduct"
        products = [ProductFactory(name=product_name) for _ in range(3)]
        for product in products:
            product.create()
        found = Product.find_by_name(product_name).all()
        self.assertEqual(len(found), 3)
        for prod in found:
            self.assertEqual(prod.name, product_name)

    def test_find_by_availability(self):
        """It should find products by availability"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.available = True
            product.create()
        unavailable_product = ProductFactory(available=False)
        unavailable_product.create()
        available_products = Product.find_by_availability(True).all()
        self.assertEqual(len(available_products), 5)
        for prod in available_products:
            self.assertTrue(prod.available)

    def test_find_by_category(self):
        """It should find products by category"""
        category = Category.FOOD
        products = [ProductFactory(category=category) for _ in range(3)]
        for product in products:
            product.create()
        found = Product.find_by_category(category).all()
        self.assertEqual(len(found), 3)
        for prod in found:
            self.assertEqual(prod.category, category)

    def test_deserialize_invalid_type_available(self):
        """It should raise DataValidationError for invalid available type"""
        product_data = {
            "name": "TestProduct",
            "description": "Invalid available type example",
            "price": "12.50",
            "available": "yes",  # invalid type
            "category": "TOOLS"
        }
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(product_data)
        self.assertIn("Invalid type for boolean [available]:", str(context.exception))

    def test_deserialize_bad_data(self):
        """It should raise DataValidationError for bad data"""
        product = Product()
        with self.assertRaises(DataValidationError) as context:
            product.deserialize("bad data")
        self.assertIn("Invalid product: body of request contained bad or no data", str(context.exception))

    def test_list_all_products(self):
        """It should list all products in the database"""
        product_list = ProductFactory.create_batch(5)
        for product in product_list:
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)
        for prod in products:
            self.assertIsNotNone(prod.id)

    def test_verify_reading_product(self):
        """It should verify if the reading functionality works correctly"""
        product = ProductFactory()
        product.create()
        retrieved_product = Product.find(product.id)
        self.assertEqual(retrieved_product.id, product.id)
        self.assertEqual(retrieved_product.name, product.name)
        self.assertEqual(retrieved_product.description, product.description)
        self.assertEqual(retrieved_product.price, product.price)
        self.assertEqual(retrieved_product.available, product.available)
        self.assertEqual(retrieved_product.category, product.category)

    def test_update_a_product_without_id(self):
        """It should raise DataValidationError if attempting to update without an ID"""
        product = ProductFactory()
        product.id = None  # Simula un prodotto senza ID
        with self.assertRaises(DataValidationError) as context:
            product.update()  # Deve sollevare DataValidationError
        self.assertEqual(str(context.exception), "Update called with empty ID field")