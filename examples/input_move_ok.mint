program init.
  var age type int.
  var name type string.
  var score type float = 0.
  var flag type bool.
  var letter type char.
initialization.
  input(age).
  input(name).
  input(flag).
  input(letter).

  move age + 10 to age.
  move age to score.
  move "Hello, " to name.

  write(age).
  write(score).
  write(name).
  write(flag).
  write(letter).
endprogram.
