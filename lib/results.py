
# classes for storing search results
import pprint
pp = pprint.PrettyPrinter(indent=4)


class Results:
	# stores all results from query (list of file results)

	def __init__(self):
		# qi is query information, output of parse2.
		self.results = []

	def add_file_result(self, file_result):
		self.results.append(file_result.get_value())

	def get_num_files(self):
		return len(self.results)

	def get_value(self):
		return self.results

class File_result:
	# a file result is a file name and a list of subquery results

	def __init__(self, file_name, num_subqueries):
		self.file_name = file_name
		# explicitly initialized each element to an empty Subquery_result so can be referenced by
		# index
		self.subquery_results = [ Subquery_result() for i in range(num_subqueries) ]

	def add_node_result(self, node_result, subquery_index):
		# add node_result to the specified subquery
		self.subquery_results[subquery_index].add_node_result(node_result)

	def get_subquery_length(self, subquery_index):
		# return length of specified subquery results
		return len(self.subquery_results[subquery_index].get_value())

	def get_value(self):
		value = {"file": self.file_name,
			"subqueries": [x.get_value() for x in self.subquery_results]}
		return value

class Subquery_result:
# 	# a subquery_result has a list of Node_results, because there can be
	# more than one node found by a particular subquery

	def __init__(self):
		self.subquery_result = []

	def add_node_result(self, node_result):
 		self.subquery_result.append(node_result.get_value())

	def get_value(self):
		return self.subquery_result

class Node_result:
	# a Node_result has a path to a hdf5 node and the values found at that node

	def __init__(self, node_name, vind_result, vtbl_result):
		# qi is query information, output of parse2.
		self.node_name = node_name
		self.vind_result = vind_result.get_value()
		self.vtbl_result = vtbl_result.get_value()

	def get_value(self):
		value = { 'node': self.node_name, 'vind': self.vind_result,
			'vtbl': self.vtbl_result }
		return value

class Vind_result:
	# Vind_result is a dict of keys (variable names) and values that are not part of a NWB 2 table

	def __init__(self):
		# qi is query information, output of parse2.
		self.vind_result = {}

	def add_vind_value(self, cloc, value):
		# cloc is name of child location, value is the value of that variable
		# store value as scalar if possible (one element), otherwise as list.
		# Add new values to previously values (make list if not already).
		assert isinstance(value, list)
		if cloc not in self.vind_result:
			if len(value) == 1:
				# save value as scalar if only one element
				self.vind_result[cloc] = value[0]
			else:
				self.vind_result[cloc] = value
		elif isinstance(self.vind_result[cloc], list):
			for val in value:
				if val not in self.vind_result[cloc]:
					self.vind_result[cloc].append(val)
		elif len(value) == 1 and value[0] == self.vind_result[cloc]:
			# scalar value already stored
			pass
		elif self.vind_result[cloc] in value:
			# scalar is in new value
			self.vind_result[cloc] = value
		else:
			# convert to list and concatenate new list
			self.vind_result[cloc] = [ self.vind_result[cloc],] + value

	def get_value(self):
		return self.vind_result

class Vtbl_result:
	# Vtbl_result is a list of row results from a NWB 2 table

	def __init__(self):
		# qi is query information, output of parse2.
		self.child_names = None
		self.row_values = None

	def set_tbl_result(self, child_names, row_values):
		# qi is query information, output of parse2.
		self.child_names = child_names
		self.row_values = row_values

	def get_value(self):
		if self.child_names is not None:
			# Line below returns results for each row as a list
			# value = {"child_names": self.child_names, "row_values": self.row_values}
			self.make_combined_value()
			value = {"child_names": self.child_names, 
				"row_values": self.row_values, "combined": self.combined_values}
		else:
			value = {}
		return value

	def make_combined_value(self):
		# generate format of results with each row a dictionary containing child: value
		combined_values = []
		for row in self.row_values:
			row_result = {}
			for i in range(len(self.child_names)):
				child_name = self.child_names[i]
				value = row[i]
				row_result[child_name] = value
			combined_values.append(row_result)
		self.combined_values = combined_values


def main():
	# test the above classes
	vtbl_res = Vtbl_result()
	vtbl_res.set_tbl_result(["id", "location"], [[1, "ca1"], [2, "DG"]])
	vind_res = Vind_result()
	vind_res.add_vind_value("start_time", "2:33pm")
	vind_res.add_vind_value("tags", "left,top,strong")
	node_result = Node_result("/epochs/trial1", vind_res, vtbl_res)
	file_result = File_result("../pynwb_examples/basic_example.nwb", 1)  # 1 subquery
	file_result.add_node_result(node_result, 0)
	results = Results()
	results.add_file_result(file_result)
	print("results are:")
	pp.pprint(results.get_value())

if __name__ == "__main__":
	main()

