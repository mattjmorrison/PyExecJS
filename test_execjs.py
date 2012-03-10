#!/usr/bin/env python3

from __future__ import unicode_literals
import sys
import io

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import doctest
import execjs


class RuntimeTestBase:
    def test_context_call(self):
        context = self.runtime.compile("id = function(v) { return v; }")
        self.assertEqual("bar", context.call("id", "bar"))

    def test_nested_context_call(self):
        context = self.runtime.compile("a = {}; a.b = {}; a.b.id = function(v) { return v; }")
        self.assertEqual("bar", context.call("a.b.id", "bar"))

    def test_context_call_missing_function(self):
        context = self.runtime.compile("")
        with self.assertRaises(execjs.ProgramError):
            context.call("missing")

    def test_exec(self):
        self.assertIsNone(self.runtime.exec_("1"))
        self.assertIsNone(self.runtime.exec_("return"))
        self.assertIsNone(self.runtime.exec_("return null"))
        self.assertIsNone(self.runtime.exec_("return function() {}"))
        self.assertIs(0, self.runtime.exec_("return 0"))
        self.assertIs(True, self.runtime.exec_("return true"))
        self.assertEqual("hello", self.runtime.exec_("return 'hello'"))
        self.assertEqual([1, 2], self.runtime.exec_("return [1, 2]"))
        self.assertEqual({"a":1,"b":2}, self.runtime.exec_("return {a:1,b:2}"))
        self.assertEqual("\\", self.runtime.exec_('return "\\\\"'))

    def test_eval(self):
        self.assertIsNone(self.runtime.eval(""))
        self.assertIsNone(self.runtime.eval(" "))
        self.assertIsNone(self.runtime.eval("null"))
        self.assertIsNone(self.runtime.eval("function(){}"))
        self.assertIs(0, self.runtime.eval("0"))
        self.assertIs(True, self.runtime.eval("true"))
        self.assertEqual([1, 2], self.runtime.eval("[1, 2]"))
        self.assertEqual([1, None], self.runtime.eval("[1, function() {}]"))
        self.assertEqual("hello", self.runtime.eval("'hello'"))
        self.assertEqual(["red", "yellow", "blue"], self.runtime.eval("'red yellow blue'.split(' ')"))
        self.assertEqual({"a":1,"b":2}, self.runtime.eval("{a:1, b:2}"))
        self.assertEqual({"a":True}, self.runtime.eval("{a:true,b:function (){}}"))
        self.assertEqual(r"\\", self.runtime.eval(r'"\\\\"'))

    def test_compile(self):
        context = self.runtime.compile("foo = function() { return \"bar\"; }")
        self.assertEqual("bar", context.exec_("return foo()"))
        self.assertEqual("bar", context.eval("foo()"))
        self.assertEqual("bar", context.call("foo"))

    def test_this_is_global_scope(self):
        self.assertIs(True, self.runtime.eval("this === (function() {return this})()"))
        self.assertIs(True, self.runtime.exec_("return this === (function() {return this})()"))

    def test_commonjs_vars_are_undefined(self):
        self.assertTrue(self.runtime.eval("typeof module == 'undefined'"))
        self.assertTrue(self.runtime.eval("typeof exports == 'undefined'"))
        self.assertTrue(self.runtime.eval("typeof require == 'undefined'"))

    def test_compile_large_scripts(self):
        body = "var foo = 'bar';\n" * 10**4
        code = "function foo() {\n" + body + "\n};\nreturn true"
        self.assertTrue(self.runtime.exec_(code))

    def test_syntax_error(self):
        with self.assertRaises(execjs.RuntimeError):
            self.runtime.exec_(")")

    def test_thrown_exception(self):
        with self.assertRaises(execjs.ProgramError):
            self.runtime.exec_("throw 'hello'")


class ExecJSTest(unittest.TestCase, RuntimeTestBase):
    def setUp(self):
        self.runtime = execjs

@unittest.FunctionTestCase
def test_runtime_available(self):
    runtime = execjs.ExternalRuntime(command=["nonexistent"],
        name=None, runner_path=None)
    
    self.assertFalse(runtime.is_available())
    
    runtime = execjs.ExternalRuntime(command=["python"],
        name=None, runner_path=None)
    self.assertTrue(runtime.is_available())
    raise Exception

for name, runtime in execjs.available_runtimes().items():
    class_name = name.capitalize() + "RuntimeTest"
    def f(runtime=runtime):
        class RuntimeTest(unittest.TestCase, RuntimeTestBase):
            def setUp(self):
                self.runtime = runtime
        RuntimeTest.__name__ = str(class_name) # 2.x compatibility
        return RuntimeTest
    exec("{class_name} = f()".format(class_name=class_name))


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(execjs))
    return tests


if __name__ == "__main__":
    unittest.main()

