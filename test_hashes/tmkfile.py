import struct

# ================================================================
# This is a sample of how to use Python to read a .tmk file written
# by the C++ code (feat2tmk.cpp, tmkfv.cpp).
# ================================================================

# tmkiotypes.h snippet:
#
# struct FeatureVectorFileHeader {
#	char projectMagic[TMK_MAGIC_LENGTH];
#	char fileTypeMagic[TMK_MAGIC_LENGTH];
#
#	// Not present in the data, but essential information on the provenance
#	// of the data.
#	char frameFeatureAlgorithmMagic[TMK_MAGIC_LENGTH];
#	int framesPerSecond;
#
#	int numPeriods; // a.k.a. P
#	int numFourierCoefficients; // a.k.a m
#
#	int frameFeatureDimension; // a.k.a d
#	int pad; // Make multiple of 16 to ease hex-dump reading
#
# };
#
# See also tmkfv.cpp.


class TMKFile:
	def __init__(self,filename):
		self.filename=filename
		self._readtmkfile(filename)
	
	
	def _readtmkfile(self,filename):
		'''
		Reads a .tmk file and prints it. See tmkiotypes.h.
		'''

		expected_project_magic = 'TMK1'
		expected_file_type_magic = 'FVEC'

		with open(filename, 'rb') as handle:
			self.project_magic = handle.read(4).decode('ascii')
			self.file_type_magic = handle.read(4).decode('ascii')
			self.frame_feature_algorithm_magic = handle.read(4).decode('ascii')

			if self.project_magic != expected_project_magic:
					msg = "File \"%s\" has project magic \"%s\" not \"%s\"." % \
						(filename, project_magic, expected_project_magic)
					raise Exception(msg)
			if self.file_type_magic != expected_file_type_magic:
					msg = "File \"%s\" has file-type magic \"%s\" not \"%s\"." % \
						(filename, file_type_magic, expected_file_type_magic)
					raise Exception(msg)

			self.frames_per_second = handle.read(4)
			self.num_periods = handle.read(4)
			self.num_fourier_coefficients = handle.read(4)
			self.frame_feature_dimension = handle.read(4)
			self.frame_feature_count = handle.read(4)

			self.frames_per_second = struct.unpack('i', self.frames_per_second)[0]
			self.num_periods = struct.unpack('i', self.num_periods)[0]
			self.num_fourier_coefficients = struct.unpack('i',
				self.num_fourier_coefficients)[0]
			self.frame_feature_dimension = struct.unpack('i',
				self.frame_feature_dimension)[0]
			self.frame_feature_count = struct.unpack('i', 
				self.frame_feature_count)[0]

			self.periods = struct.unpack('i' * self.num_periods,
				handle.read(4 * self.num_periods))


			self.fourier_coefficients = struct.unpack('f' * self.num_fourier_coefficients,
					handle.read(4 * self.num_fourier_coefficients))


			self.pure_average_feature = struct.unpack('f' * self.frame_feature_dimension,
					handle.read(4 * self.frame_feature_dimension))

			#TODO: The following may not be right.
			#Look back at https://github.com/facebook/ThreatExchange/blob/master/tmk/cpp/tools/tmkdump.py
			#Not important for our use; so, just ignoring
			#for i in range(0, num_periods):
			#		for j in range(0, num_fourier_coefficients):
			#			self.cos_feature = struct.unpack('f' * frame_feature_dimension,
			#				handle.read(4 * frame_feature_dimension))
			#for i in range(0, num_periods):
			#		for j in range(0, num_fourier_coefficients):
			#			self.sin_feature = struct.unpack('f' * frame_feature_dimension,
			#				handle.read(4 * frame_feature_dimension))
		
	def to_s(self):
		print("filename							%s" % self.filename)
		print("project_magic					%s" % self.project_magic)
		print("file_type_magic					%s" % self.file_type_magic)
		print("frame_feature_algorithm_magic %s" % self.frame_feature_algorithm_magic)
		print("frames_per_second				%d" % self.frames_per_second)
		print("num_periods						%d" % self.num_periods)
		print("num_fourier_coefficients		%d" % self.num_fourier_coefficients)
		print("frame_feature_dimension		%d" % self.frame_feature_dimension)
		print("frame_feature_count			%d" % self.frame_feature_count)
		print(self.periods)
		print(self.fourier_coefficients)
		print(self.pure_average_feature) #This is the only feature we really care about
		#print("cos:%d:%d " % (i, j), end='')
		#print(self.cos_feature)
		#print("sin:%d:%d " % (i, j), end='')
		#print(self.sin_feature)

if __name__ == "__main__":
	import sys
	import errno
	try:
		for filename in sys.argv[1:]:
			f=TMKFile(filename)
			print(f.to_s())
			#print(f.pure_average_feature)
	except IOError as e:
		if e.errno == errno.EPIPE:
			pass  # e.g. we were piped to head which is harmless
		else:
			raise e
